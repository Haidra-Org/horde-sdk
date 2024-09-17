# Contributing to horde_sdk

## Code Quality Tools

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
  - See all rules (but not necessarily used in the project) availible in rust [here](https://beta.ruff.rs/docs/rules/).
* [mypy](https://mypy-lang.org/)
  - Static type safety
  - I recommending using the [mypy daemon](https://mypy.readthedocs.io/en/stable/mypy_daemon.html) instead of periodically running `pre-commit` (or `mypy` directly.).
    - If you are using VSCode, I recommend the `matangover.mypy` extension, which implements this nicely.

## Things to know

  * The `AI_HORDE_DEV_URL` environment variable overrides `AI_HORDE_URL`. This is useful for testing changes locally.
  * pytest files which end in `_api_calls.py` run last, and never run during the CI. It is currently incumbent on individual developers to confirm that these tests run successfully locally. In the future, part of the CI will be to spawn an AI-Horde and worker instances and test it there.


## Verifying the horde SDK API surface

You can run the following:

```bash
pytest -m "object_verify"
```

This will run the tests which validate the objects defined in the SDK are:
- In the appropriate place
- Match the live API (or if `AI_HORDE_DEV_URL` that version of the API)
- That the models are exposed via `__init__.py`
- And will run any other tests which ensure internal consistency.
  - This generally does not include specific object validation beyond what can be automatically derived directly from the API docs or from general conventions from the SDK itself.
  - If adding objects, you should add tests more specific to the expected functionality of that endpoint and the `object_verify` tests should only be treated as the bare-minimum.

## When the API adds an endpoint or changes a model
With the top level directory (the one that contains `pyproject.toml`) as your working directory:
```bash
python horde_sdk/scripts/write_all_payload_examples_for_tests.py
python horde_sdk/scripts/write_all_response_examples_for_tests.py
python docs/build_docs.py
```
This will update the data found in `tests/test_data/` from the default horde URL, or if any of the override environment variables are set, from there.

Running `build_docs.py` will update any automatically generated mkdocs documentation stubs or resources (such as the API Model <-> SDK Model map).

Be sure to run the test suite (without any `*_api_calls.py` tests) after. You may also may want to just start with `pytest -m "object_verify"` (see also the section on verifying the horde SDK API surface).
