# Contributing to horde_sdk

## Table of Contents

- [Contributing to horde\_sdk](#contributing-to-horde_sdk)
    - [Table of Contents](#table-of-contents)
    - [Environment Management](#environment-management)
        - [First time setup](#first-time-setup)
    - [Code Quality Tools](#code-quality-tools)
    - [Code Style and System Design](#code-style-and-system-design)
    - [Testing](#testing)
        - [When the API adds an endpoint or changes a model](#when-the-api-adds-an-endpoint-or-changes-a-model)
        - [Verifying the horde SDK API surface](#verifying-the-horde-sdk-api-surface)
    - [New Features/Pull Requests/Working on issues](#new-featurespull-requestsworking-on-issues)
        - [Pull Request Do's and Don'ts](#pull-request-dos-and-donts)
            - [Do](#do)
            - [Don't](#dont)
        - [Before Requesting Review](#before-requesting-review)
    - [Releasing](#releasing)

## Environment Management

[uv](https://github.com/astral-sh/uv/) is the suggested python environment management tool.

### First time setup

- Install uv, as described [in their documentation](https://github.com/astral-sh/uv/#installation).
- `uv python install 3.12 3.13`
- `uv self update`
- `uv sync --all-groups`
- The `.venv/` directory will now be created with all project, development and documentation dependencies installed.
    - Be sure to point your IDE to the python binary appropriate for your OS in this directory.

## Code Quality Tools

- [**pre-commit**](https://pre-commit.com/)
    - Creates virtual environments for formatting and linting tools
    - Run `pre-commit run --all-files` or see `.pre-commit-config.yaml` for more info.

> Note: Many of the tools below are run by `pre-commit` automatically, but can also be run manually if desired.

- [**ruff**](https://github.com/astral-sh/ruff)
    - Linting rules from a wide variety of selectable rule sets
    - See `pyproject.toml` for the rules used.
    - See all rules (but not necessarily used in the project) [available in ruff here](https://beta.ruff.rs/docs/rules/).
    - Run with `ruff check .`
        - Note: When using autofixing (`ruff check . --fix`), changes may be made that require running black, which can then result in needing to run `ruff check . --fix` again.
        - Consider running `black . && ruff check . --fix && black . && ruff check . --fix` to avoid this.
- [**mypy**](https://mypy-lang.org/)
    - Static type safety
    - I recommending using the [mypy daemon](https://mypy.readthedocs.io/en/stable/mypy_daemon.html) instead of periodically running `pre-commit` (or `mypy` directly.).
- [**pyright**](https://github.com/microsoft/pyright)
    - Shipped with vscode by default (via the python extension `ms-python.vscode-pylance`)
    - Suggested settings:
        - `"python.analysis.typeCheckingMode": "off"`
            - The pylance extension has certain opinionated type checking assertions which are clash with mypy.
            - For example, overriding an optional field to be non-optional is considered by pylance to be a type error due to the field being invariant and the parent class potentially settings it to `None`. However, by convention in the SDK, this is a forbidden pattern.
        - `"python.analysis.languageServerMode": "full"`
        - `"python.testing.pytestEnabled": true`
- [**tach**](https://github.com/gauge-sh/tach)
    - Enforces internal namespace dependency constraints. This helps avoid circular dependencies and helps ensure implementations are in a logical place.

## Code Style and System Design

See the [style guide in the docs folder](docs/concepts/style_guide.md) or go to the [same place in the horde_sdk documentation](https://horde-sdk.readthedocs.io/en/latest/) for more information on the code style requirements and design patterns used in the SDK.

## Testing

- horde_sdk uses [pytest](https://docs.pytest.org/en/stable/) for testing.
- The `AI_HORDE_DEV_URL` environment variable overrides `AI_HORDE_URL`. This is useful for testing changes locally.
- pytest files which end in `_api_calls.py` run last, and never run during the CI. It is currently incumbent on individual developers to confirm that these tests run successfully locally. In the future, part of the CI will be to spawn an AI-Horde and worker instances and test it there.
- **_Rationale_**: Local runs of the test suite benefit from a way to avoid running tests dependent on a live API.

Tests run in the project's `uv` environment (no separate virtualenv is needed):

```bash
# Run the suite the same way CI does (excludes the live-API tests)
uv run pytest tests --ignore-glob='**/*api_calls*' -m "not api_side_ci"

# Run the full local suite, including the live-API (*_api_calls.py) tests
uv run pytest tests -m "not api_side_ci"

# Run formatting, linting, and type checks (the pre-commit hooks)
uv run pre-commit run --all-files
```

CI exercises the matrix of supported Python versions; to reproduce a specific
interpreter locally, prefix any of the above with `--python`, e.g.
`uv run --python 3.12 pytest ...`.

### When the API adds an endpoint or changes a model

With the top level directory (the one that contains `pyproject.toml`) as your working directory:

```bash
python horde_sdk/scripts/write_all_payload_examples_for_tests.py
python horde_sdk/scripts/write_all_response_examples_for_tests.py
python docs/build_docs.py
```

This will update the data found in `tests/test_data/` from the default horde URL, or if any of the override environment variables are set, from there. This includes writing example payloads and responses extrapolated from the live APIs.

Running `build_docs.py` will update any automatically generated mkdocs documentation stubs or resources (such as the API Model <-> SDK Model map).

Be sure to run the test suite (without any `*_api_calls.py` tests) after. You may also may want to just start with `pytest -m "object_verify"` (see also the section on verifying the horde SDK API surface).

### Verifying the horde SDK API surface

You can run the following:

```bash
pytest -m "object_verify" -s
```

> Note: The `-s` flag is important as it allows you to see the output of the tests, which can be helpful for debugging. Often, the tests will also print out corrective actions to take if the tests fail.

## New Features/Pull Requests/Working on issues

The Horde ecosystem is a collaborative effort made possible through volunteer effort. We welcome all contributions and permission is not needed to work on issues or submit pull requests. However, if there is activity on an issue, you should consider reaching out to that person to coordinate efforts and avoid duplicate/conflicting work. Additionally, please considering commenting on an issue to let others know you are working on it.

### Pull Request Do's and Don'ts

#### Do

- Be bold in your contribution
- Ensure your code complies with the [code style and system design](#code-style-and-system-design) guidelines
- Open draft pull requests when you want early feedback on your approach
- Include clear descriptions of changes made and reasoning behind them
- Include tests for any new features or bug fixes
- Update documentation for new features or changes to existing functionality
- Use descriptive commit messages consistent with the project commit history, especially for medium-to-large changesets.
    - While it is possible we will squash commits before merging, it is still helpful to have descriptive commit messages for review and opens the possibility of rebasing instead.

#### Don't

- Make large sweeping changes unrelated to your primary goal
- Include unnecessary changes like formatting or edits to unrelated files (open a separate PR for this)

### Before Requesting Review

- Ensure your PR is based on the latest `main` branch (rebase if out of date)
- Verify all tests and code quality checks pass against the intended API versions
- Double-check that all necessary documentation is updated, including docstrings and the relevant markdown files in the `docs` directory.

## Releasing

Releases are cut by pushing a version tag to `main` — there are no version files to bump by hand. The package version is derived from the tag at build time by [setuptools-scm](https://github.com/pypa/setuptools_scm), so a tag of `v1.2.3` produces version `1.2.3`.

To publish a new release (maintainers with tag-push access only):

1. Ensure `main` is green (tests and the lint/type-check workflow pass) and up to date locally:

   ```bash
   git checkout main && git pull
   ```

2. Create and push a `vX.Y.Z` tag on the release commit:

   ```bash
   git tag v1.2.3        # or: git tag -a v1.2.3 -m "..." for an annotated tag
   git push origin v1.2.3
   ```

3. Pushing the tag triggers the `horde_sdk build and publish` workflow, which:
   - builds the sdist and wheel with `uv build` (versioned from the tag),
   - publishes them to [PyPI](https://pypi.org/p/horde-sdk/) via trusted publishing (no API token required), and
   - creates a GitHub release with auto-generated notes.

> Note: `horde_sdk/_version.py` is generated by setuptools-scm and should not be edited or committed by hand.
