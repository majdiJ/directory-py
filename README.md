# directory-py

An extremely simple python command-line script that prints the file and folder structure of a directory, with support for ignoring files and folders via a `.directorypyignore` file.

Useful for quickly generating a directory structure for documentation purposes or for agentic coding.

No third-party libraries required.

## Usage

```bash
# Run from the script's own directory
python list_directory.py

# Run on a specific directory
python list_directory.py /path/to/folder
```

When run, it will ask how many levels deep to display:

```
Enter the number of layers deep to display (0 for unlimited):
```

## Ignoring files and folders

Create a `.directorypyignore` file in the root of the directory being scanned. It works just like a `.gitignore` - one pattern per line.

```
# Ignore compiled Python files
__pycache__/
*.pyc

# Ignore dependency folders
node_modules/
.venv/

# Ignore a specific file
secrets.json
```

Supported syntax:

| Pattern | Behaviour |
|---|---|
| `*.pyc` | Match any file with that extension |
| `build/` | Match a directory only |
| `/dist` | Match only at the root level |
| `docs/**/*.md` | Match files in nested subdirectories |
| `!important.log` | Un-ignore a previously ignored file |
| `# comment` | Ignored line |

If no `.directorypyignore` is found, all files are shown.