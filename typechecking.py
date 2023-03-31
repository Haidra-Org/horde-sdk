"""Performs any type-related checking/linting."""
import os
import subprocess
import sys


def main() -> None:  # noqa: D103
    currentDirectory = os.path.dirname(os.path.abspath(__file__))

    print(f"type checking base dir: {currentDirectory}")
    try:
        subprocess.run("python -s -m mypy --install-types", shell=True, check=True)
        subprocess.run("python -s -m mypy ./src/", shell=True, check=True)
    except subprocess.CalledProcessError:
        print("mypy exited with an error!")
        sys.exit(1)


if __name__ == "__main":
    main()
