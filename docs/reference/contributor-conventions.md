---
title: "Contributor conventions"
summary: "Collect SDK naming, typing, model, test, documentation, and generated-file requirements."
topics: [architecture, contributing]
order: 80
---

# Contributor conventions

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [contributing](../topics.md#contributing)
<!-- END GENERATED: topics -->

Repository-wide Python and documentation rules come from the shared Haidra standards. SDK changes also preserve typed
endpoint metadata and deterministic generated reference output.

## Required workflow

1. Make behavior, tests, and documentation changes together.
2. Run `uv run pre-commit run --all-files` and the affected tests.
3. Run `uv run python docs/build_docs.py generate` after changing included modules or request metadata.
4. Run `uv run python docs/check_docs.py --fast` before committing documentation.
5. Run `uv run python docs/build_site.py --clean --strict` for changes affecting rendered structure or links.

Public modules, classes, methods, fields, and variables use Google-style docstrings. Request classes declare endpoint,
method, model name, and successful response types as class methods. Pydantic aliases preserve wire compatibility while
Python names follow snake case.

## Code map

| Rule | Source |
| --- | --- |
| Python conventions | `docs/haidra-assets/docs/meta/python.md` |
| Documentation conventions | `docs/haidra-assets/docs/meta/documentation.md` |
| Pull-request conventions | `docs/haidra-assets/docs/meta/pull_requests.md` |
| API reference generation | `docs/build_docs.py`, `main` |
| Documentation fast checks | `docs/check_docs.py`, `main` |

Generated pages and indexes are reviewed as tracked output. CI rejects drift, broken code references, em dashes in
curated prose, unresolved internal links, and front matter that renders as page text.
