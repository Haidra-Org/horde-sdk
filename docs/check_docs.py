"""Run fast, cross-platform documentation checks shared by pre-commit and CI."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"


def curated_markdown() -> list[Path]:
    """Return authored and planned Markdown, excluding generated and vendored corpora."""
    paths = [DOCS_ROOT / "README.md", DOCS_ROOT / "topics.md"]
    for directory in ("tutorial", "how-to", "reference", "explanation"):
        paths.extend(sorted((DOCS_ROOT / directory).glob("*.md")))
    return paths


def run(command: list[str]) -> int:
    """Run one check from the repository root and preserve its output."""
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def check_em_dashes(paths: list[Path]) -> int:
    """Report em dashes in curated prose."""
    found = False
    for path in paths:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "—" in line:
                print(f"{path.relative_to(PROJECT_ROOT)}:{number}: em dash in curated prose", file=sys.stderr)
                found = True
    return int(found)


def main(argv: list[str] | None = None) -> int:
    """Run the fast documentation gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fast", action="store_true", help="Accepted for an explicit, stable contributor command")
    parser.parse_args(argv)

    curated = curated_markdown()
    commands = [
        [sys.executable, "docs/build_docs.py", "--check"],
        [
            sys.executable,
            "docs/haidra-assets/tools/gen_doc_index.py",
            "docs",
            "--check",
            "--nav",
            "zensical.toml",
        ],
        [
            sys.executable,
            "docs/haidra-assets/tools/check_code_refs.py",
            *[str(path) for path in curated],
            "--roots",
            "horde_sdk,tests,docs,examples",
        ],
    ]
    failed = check_em_dashes(curated)
    for command in commands:
        failed |= int(run(command) != 0)
    if failed:
        return 1
    print(f"Fast documentation checks passed ({len(curated)} curated files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
