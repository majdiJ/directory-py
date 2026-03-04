import os
import re

IGNORE_FILE = ".directorypyignore"

def _pattern_to_regex(pattern):
    """Convert a single gitignore-style pattern into a compiled regex."""
    # A pattern is "anchored" (only matches from root) if it contains a /
    # anywhere other than at the very end
    anchored = '/' in pattern.rstrip('/')

    # Remove a leading slash — it just signals anchoring, which we handle above
    if pattern.startswith('/'):
        pattern = pattern[1:]

    result = ''
    i = 0
    while i < len(pattern):
        c = pattern[i]

        if c == '*':
            if i + 1 < len(pattern) and pattern[i + 1] == '*':
                # Double star: **
                i += 2
                if i < len(pattern) and pattern[i] == '/':
                    # **/ matches zero or more directory segments
                    i += 1
                    result += '(?:[^/]+/)*'
                else:
                    # ** at end matches everything
                    result += '.*'
                continue
            else:
                # Single star: matches anything except a path separator
                result += '[^/]*'

        elif c == '?':
            # Matches any single character except a path separator
            result += '[^/]'

        elif c == '[':
            # Character class — find the closing bracket and pass it through
            j = pattern.find(']', i + 1)
            if j == -1:
                result += re.escape('[')
            else:
                result += pattern[i:j + 1]
                i = j  # will be incremented at end of loop

        else:
            result += re.escape(c)

        i += 1

    if anchored:
        # Must match from the start of the relative path
        return re.compile('^' + result + '(/.*)?$')
    else:
        # Can match at any depth
        return re.compile('(^|/)' + result + '(/.*)?$')


def load_ignore_patterns(root_dir):
    """
    Load .directorypyignore from root_dir and return a list of
    (compiled_regex, is_negated, dir_only) tuples.
    """
    ignore_file_path = os.path.join(root_dir, IGNORE_FILE)
    if not os.path.exists(ignore_file_path):
        return []

    rules = []
    with open(ignore_file_path, "r") as f:
        for line in f:
            pattern = line.rstrip('\n')

            # Strip inline comments (a space followed by #)
            if ' #' in pattern:
                pattern = pattern[:pattern.index(' #')]

            pattern = pattern.strip()

            # Skip empty lines and full-line comments
            if not pattern or pattern.startswith('#'):
                continue

            # Negation rule (un-ignores a previously ignored path)
            negated = pattern.startswith('!')
            if negated:
                pattern = pattern[1:]

            # Trailing slash means the rule only applies to directories
            dir_only = pattern.endswith('/')
            if dir_only:
                pattern = pattern.rstrip('/')

            try:
                regex = _pattern_to_regex(pattern)
                rules.append((regex, negated, dir_only))
            except re.error:
                # If a pattern is malformed, skip it silently
                continue

    return rules


def is_ignored(full_path, root_dir, rules, is_dir):
    """
    Walk through all rules in order (later rules override earlier ones)
    and return True if the path should be ignored.
    """
    if not rules:
        return False

    relative_path = os.path.relpath(full_path, root_dir).replace(os.sep, '/')
    ignored = False

    for regex, negated, dir_only in rules:
        # dir_only rules don't apply to files
        if dir_only and not is_dir:
            continue
        if regex.search(relative_path):
            ignored = not negated  # negation flips the ignored state

    return ignored


def list_directory_structure(root_dir, root, rules, indent_level=0, max_depth=float('inf'), current_depth=0):
    if current_depth > max_depth:
        print(' ' * indent_level + '|-- ...')
        return

    try:
        items = os.listdir(root_dir)
    except PermissionError:
        print(' ' * indent_level + '|-- [permission denied]')
        return

    items.sort()

    for item in items:
        full_path = os.path.join(root_dir, item)
        item_is_dir = os.path.isdir(full_path)

        if is_ignored(full_path, root, rules, item_is_dir):
            continue

        print(' ' * indent_level + '|-- ' + item)

        if item_is_dir:
            list_directory_structure(full_path, root, rules, indent_level + 4, max_depth, current_depth + 1)


def main():
    current_directory = os.getcwd()

    # Load ignore rules from .directorypyignore if it exists
    rules = load_ignore_patterns(current_directory)

    if rules:
        print(f"Loaded {len(rules)} ignore rule(s) from '{IGNORE_FILE}'")
    else:
        print(f"No '{IGNORE_FILE}' found (or it's empty) — showing all files.")

    user_input = input("Enter the number of layers deep to display (0 for unlimited): ").strip()

    if user_input == '0':
        max_depth = float('inf')
    else:
        try:
            max_depth = int(user_input)
            if max_depth < 0:
                print("Please enter a non-negative number.")
                return
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            return

    print(f"\nDirectory structure of: {current_directory}\n")
    print(f"{current_directory}")

    list_directory_structure(current_directory, current_directory, rules, max_depth=max_depth)


if __name__ == "__main__":
    main()