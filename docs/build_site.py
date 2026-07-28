"""Build the Zensical site with an optional host-specific canonical URL."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "zensical.toml"
SITE_URL_PATTERN = re.compile(r'^site_url = "[^"]+"$', re.MULTILINE)


def canonical_url(value: str) -> str:
    """Validate and normalize a canonical site URL."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("site URL must be an absolute HTTP(S) URL")
    return value if value.endswith("/") else f"{value}/"


def temporary_config(site_url: str) -> Path:
    """Write a root-local temporary config so relative project paths remain valid."""
    original = CONFIG_PATH.read_text(encoding="utf-8")
    rendered, count = SITE_URL_PATTERN.subn(f'site_url = "{site_url}"', original, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace site_url in {CONFIG_PATH}")
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=".zensical-build-",
        suffix=".toml",
        dir=PROJECT_ROOT,
        delete=False,
    ) as handle:
        handle.write(rendered)
        return Path(handle.name)


def main(argv: list[str] | None = None) -> int:
    """Build through the installed Zensical executable."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="Discard Zensical's build cache")
    parser.add_argument("--strict", action="store_true", help="Fail on build warnings")
    parser.add_argument("--site-url", type=canonical_url, help="Override the canonical URL for this build only")
    args = parser.parse_args(argv)

    config_path = CONFIG_PATH
    temporary_path: Path | None = None
    try:
        if args.site_url:
            temporary_path = temporary_config(args.site_url)
            config_path = temporary_path
        command = ["zensical", "build", "--config-file", str(config_path)]
        if args.clean:
            command.append("--clean")
        if args.strict:
            command.append("--strict")
        return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
