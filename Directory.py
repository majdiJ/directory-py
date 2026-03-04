import os
import re
import sys
import argparse

IGNORE_FILE = ".directorypyignore"
DEFAULT_EXPORT_FILENAME = "dirpy_structure.txt"


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
        return re.compile('^' + result + '(/.*)?$')
    else:
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
        if dir_only and not is_dir:
            continue
        if regex.search(relative_path):
            ignored = not negated

    return ignored


def list_directory_structure(root_dir, root, rules, write, indent_level=0, max_depth=float('inf'), current_depth=0):
    """
    Recursively list directory structure, calling write() for each line.
    write() is either print (console) or a file-writing function, or both.
    """
    if current_depth > max_depth:
        write(' ' * indent_level + '|-- ...')
        return

    try:
        items = os.listdir(root_dir)
    except PermissionError:
        write(' ' * indent_level + '|-- [permission denied]')
        return

    items.sort()

    for item in items:
        full_path = os.path.join(root_dir, item)
        item_is_dir = os.path.isdir(full_path)

        if is_ignored(full_path, root, rules, item_is_dir):
            continue

        write(' ' * indent_level + '|-- ' + item)

        if item_is_dir:
            list_directory_structure(full_path, root, rules, write, indent_level + 4, max_depth, current_depth + 1)


def main():
    parser = argparse.ArgumentParser(
        description="List a directory structure, with optional .directorypyignore support."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Directory to scan (defaults to the script's own directory)."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Export the structure to a text file."
    )
    parser.add_argument(
        "--save-path",
        default=None,
        metavar="FILE",
        help="Path for the exported text file (only used with --save). "
             f"Defaults to {DEFAULT_EXPORT_FILENAME} in the script's directory."
    )
    args = parser.parse_args()

    # Resolve the directory to scan
    if args.path:
        current_directory = os.path.abspath(args.path)
        if not os.path.isdir(current_directory):
            print(f"Error: '{args.path}' is not a valid directory.")
            sys.exit(1)
    else:
        current_directory = os.path.dirname(os.path.abspath(__file__))

    # Resolve export path if --save was given
    export_path = None
    if args.save:
        if args.save_path:
            export_path = os.path.abspath(args.save_path)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            export_path = os.path.join(script_dir, DEFAULT_EXPORT_FILENAME)

    # Load ignore rules
    rules = load_ignore_patterns(current_directory)

    if rules:
        print(f"Loaded {len(rules)} ignore rule(s) from '{IGNORE_FILE}'")
    else:
        print(f"No '{IGNORE_FILE}' found (or it's empty) — showing all files.")

    # Ask for depth
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

    # Build the header line
    header = f"Directory structure of: {current_directory}"

    # Set up the write function — prints to console, and also writes to file if --save
    if export_path:
        export_file = open(export_path, "w", encoding="utf-8")

        def write(line):
            print(line)
            export_file.write(line + "\n")
    else:
        export_file = None

        def write(line):
            print(line)

    print()
    write(header)
    write(current_directory)

    list_directory_structure(current_directory, current_directory, rules, write, max_depth=max_depth)

    if export_file:
        export_file.close()
        print(f"\nStructure saved to: {export_path}")


if __name__ == "__main__":
    main()