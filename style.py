"""Enforce linting and formatting rules."""
import argparse
import glob
import os
import subprocess
import sys


def main(fix: bool | None = None) -> None:  # noqa: D103
    # Set the working directory to where this script is located
    currentDirectory = os.path.dirname(os.path.abspath(__file__))

    os.chdir(currentDirectory)

    src = ["src/", "tests/"]

    ignore_src: list[str] = []

    root_folder_src = glob.glob("*.py")

    src.extend(root_folder_src)

    src = [item for item in src if item not in ignore_src]

    class _args:
        fix: bool

    args: _args | argparse.Namespace

    if fix is None:
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument(
            "--fix",
            action="store_true",
            required=False,
            help="Fix issues which can be fixed automatically",
        )
        args = arg_parser.parse_args()
    else:
        args = _args()
        args.fix = fix

    black_args = [
        "black",
        "--line-length=119",
    ]

    ruff_args = ["ruff"]

    if args.fix:
        print("fix requested")
        ruff_args.extend(("check", "--fix"))
    else:
        print("fix not requested")

        black_args.append("--check")
        black_args.append("--diff")

    lint_processes = [ruff_args, black_args]

    print(f"linting base directory: {currentDirectory}")
    for process_args in lint_processes:
        process_args.extend(src)

        command = " ".join(process_args)
        print(f"\nRunning {command}")
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError:
            print("Linting Failed! Not all linters may have run before the failure.")
            sys.exit(1)


if __name__ == "__main__":
    main()
