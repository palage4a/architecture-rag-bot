import os
import re
import json
import argparse
from faker import Faker

fake = Faker()

def main():
    parser = argparse.ArgumentParser(description="Generate JSON mapping from markdown H1 headings to fake names")
    parser.add_argument("--input-dir", default="knowledge_base/", help="Directory with markdown files")
    parser.add_argument("--output", default="mapping.json", help="Output JSON file")
    args = parser.parse_args()

    mapping = {}

    for filename in os.listdir(args.input_dir):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(args.input_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            key = match.group(1).strip()
            mapping[key] = fake.name()

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"Generated mapping for {len(mapping)} entries in {args.output}")

if __name__ == "__main__":
    main()