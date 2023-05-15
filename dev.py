"""Helper file containing some useful tools for contributing."""
import argparse
import glob
import os
import pathlib
import shutil
import subprocess
import sys


def main() -> None:  # noqa: D103
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-p",
        "--precommit",
        action="store_true",
        required=False,
        help="Runs all pre-commit checks.",
    )
    arg_parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        required=False,
        help="Runs all pre-commit checks and attempts any available automatic fix.",
    )
    arg_parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        required=False,
        help="Runs all unit tests.",
    )

    arg_parser.add_argument(
        "-c",
        "--config_dev",
        action="store_true",
        required=False,
        help="Configures your environment for developing this package.",
    )
    arg_parser.add_argument(
        "--clean",
        action="store_true",
        required=False,
        help="Cleans some caches that can cause issues during development.",
    )

    args = arg_parser.parse_args()

    if len(sys.argv) <= 1:
        arg_parser.print_help()

    if (args.precommit or args.fix) and (args.test or args.config_dev or args.clean):
        arg_parser.print_help()

    def confirm_prompt(question: str) -> bool:
        reply = None
        while reply not in ("y", "n"):
            reply = input(f"{question} (y/n): ").casefold()
        return reply == "y"

    currentDirectory = os.path.dirname(os.path.abspath(__file__))

    if args.precommit or args.fix:
        import style
        import typechecking

        typechecking.main()
        style.main(args.fix)

    elif args.clean:
        base_caches_to_remove = [".mypy_cache", ".pytest_cache"]
        caches_to_remove: list[str] = [cache for cache in base_caches_to_remove if pathlib.Path(cache).exists()]

        caches_to_remove.extend(glob.glob("./**/__pycache__", recursive=True))
        for cache in caches_to_remove:
            print(cache)

        if len(caches_to_remove) == 0:
            print("No caches found!")
            return

        if confirm_prompt("Delete the above files?"):
            for cache in caches_to_remove:
                shutil.rmtree(cache)

    elif args.test:
        subprocess.run("pytest")

    elif args.config_dev:
        os.chdir(currentDirectory)
        dev_setup_commands = [
            "pip install -r requirements.dev.txt",
            "pip install -r requirements.txt",
            "mypy --install-types",
            "pip install -e .",
        ]

        for command in dev_setup_commands:
            print(command)
        print()
        print("-> Double check that you're in a virtual environment!")
        print(f"-> These commands will happen in: {currentDirectory}")

        if confirm_prompt("Run the above commands?"):
            for command in dev_setup_commands:
                subprocess.run(command)
                pass


if __name__ == "__main__":
    main()
