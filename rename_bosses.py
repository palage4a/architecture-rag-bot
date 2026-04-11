import argparse
import json
import os
import re
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description="Rename boss files and replace boss names in content")
    parser.add_argument("-m", "--mapping", default="mapping.json", help="Path to mapping JSON file")
    parser.add_argument("-d", "--directory", default="knowledge_base/", help="Target directory")
    parser.add_argument("--backup", action="store_true", help="Create a backup of the directory before making changes")
    args = parser.parse_args()

    # Load mapping
    with open(args.mapping, "r") as f:
        mapping = json.load(f)

    # Create backup if requested
    if args.backup:
        backup_dir = args.directory.rstrip("/") + "_backup"
        if os.path.exists(args.directory):
            shutil.copytree(args.directory, backup_dir)
            print(f"Backup created: {backup_dir}", file=sys.stderr)

    # First, handle file renaming
    for old_name, new_name in mapping.items():
        old_filename = old_name.replace(" ", "_") + ".md"
        new_filename = new_name.replace(" ", "_") + ".md"

        old_path = os.path.join(args.directory, old_filename)
        new_path = os.path.join(args.directory, new_filename)

        try:
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                print(f"Renamed: {old_filename} -> {new_filename}")
            else:
                print(f"File not found: {old_filename}")
        except PermissionError as e:
            print(f"Error renaming {old_filename}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error renaming {old_filename}: {e}", file=sys.stderr)

    # Now iterate through all .md files ONCE and check against ALL mappings
    for filename in os.listdir(args.directory):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(args.directory, filename)

        try:
            with open(filepath, "r") as f:
                content = f.read()
        except PermissionError as e:
            print(f"Error reading {filename}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error reading {filename}: {e}", file=sys.stderr)
            continue

        original_content = content
        total_replacements = 0

        # Check against ALL mappings for this file
        for old_name, new_name in mapping.items():
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(old_name) + r'\b'
            matches = re.findall(pattern, content)
            if matches:
                new_content = re.sub(pattern, new_name, content)
                total_replacements += len(matches)
                content = new_content

        # Write file only if changes were made
        if content != original_content:
            try:
                with open(filepath, "w") as f:
                    f.write(content)
                print(f"Replaced {total_replacements} occurrence(s) in {filename}")
            except PermissionError as e:
                print(f"Error writing {filename}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error writing {filename}: {e}", file=sys.stderr)

    print("Done")


if __name__ == "__main__":
    main()