# Contributing to horde_sdk

Here are a list of code quality tools this project uses:

* [tox](https://tox.wiki/)
  - Creates virtual environments for CI or local pytest runs.
    - Note that the CI does not current execute calls to the production API by default.
  - Run `tox list` or see `tox.ini` for more info
* [pre-commit](https://pre-commit.com/)
  - Creates virtual environments for formatting and linting tools
  - Run `pre-commit run --all-files` or see `.pre-commit-config.yaml` for more info.
* [black](https://github.com/psf/black)
  - Whitespace formatter
* [ruff](https://github.com/astral-sh/ruff)
  - Linting rules from a wide variety of selectable rule sets
  - See `pyproject.toml` for the rules used.
  - See *all* rules availible in rust [here](https://beta.ruff.rs/docs/rules/).
* [mypy](https://mypy-lang.org/)
  - Static type safety
  - I recommending using the [mypy daemon](https://mypy.readthedocs.io/en/stable/mypy_daemon.html).
    - If you are using VSCode, I recommend the `matangover.mypy` extension, which implements this nicely.
