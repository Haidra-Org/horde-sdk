import argparse
import os
import re
import sys


def main(path: str) -> None:
    print(f"Processing {path}")
    with open(path, encoding="utf-8") as f:
        contents = f.read()
    contents = re.sub(r"example=([^=]*?)(,)?(\)|$)", r"examples=[\1]\2\3", contents)
    contents = re.sub(r"example=\"(.*)\"(,)", r'examples=["\1"]\2', contents)
    contents = re.sub(r"example=(\d*)(,|$|\))", r"examples=[\1]\2", contents)
    contents = re.sub(r"example=(\d*\.\d)(,|$|\))", r"examples=[\1]\2", contents)

    contents = contents.replace("id: ", "id_: ")
    contents = contents.replace("type: ", "type_: ")
    # Replace the literal string `\n` with a newline

    with open(path, "w", encoding="utf-8") as f:
        f.write(contents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the file to fix")
    args = parser.parse_args()
    path = args.path
    if not os.path.exists(path):
        print(f"Path {path} does not exist")
        sys.exit(1)

    main(path)
