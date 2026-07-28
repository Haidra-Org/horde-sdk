"""Generate the tracked SDK API reference and endpoint map.

Run ``python docs/build_docs.py generate`` after adding an included module or changing
request metadata. CI runs ``python docs/build_docs.py --check`` and fails when the
tracked output differs from the source tree.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from horde_sdk.generic_api.apimodels import HordeRequest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_ROOT = PROJECT_ROOT / "horde_sdk"
API_DOCS_ROOT = PROJECT_ROOT / "docs" / "reference" / "api" / "horde_sdk"
ENDPOINT_MAP_PATH = PROJECT_ROOT / "docs" / "reference" / "endpoint-map.md"

# Executing a script inside docs/ puts that directory first on sys.path. The previous
# generated corpus also used a top-level docs/horde_sdk directory, which can otherwise
# shadow the real package while it is being removed during migration.
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

INCLUDED_ROOT_MODULES = frozenset(
    {
        "horde_sdk.consts",
        "horde_sdk.exceptions",
        "horde_sdk.horde_logging",
        "horde_sdk.localize",
        "horde_sdk.safety",
        "horde_sdk.utils.image_utils",
    },
)
INCLUDED_PREFIXES = (
    "horde_sdk.ai_horde_api.",
    "horde_sdk.backend_parsing.",
    "horde_sdk.generation_parameters.",
    "horde_sdk.generic_api.",
    "horde_sdk.ratings_api.",
    "horde_sdk.worker.",
)
EXCLUDED_MODULES = frozenset(
    {
        "horde_sdk.generic_api._reflection",
    },
)

# These are the entry points where seeing inherited behavior is worth the extra page
# density. Every other generated page renders declared members only.
EXPANDED_OBJECTS = (
    "horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncClientSession",
    "horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncManualClient",
    "horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncSimpleClient",
    "horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIClientSession",
    "horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIManualClient",
    "horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPISimpleClient",
    "horde_sdk.worker.generations.AlchemySingleGeneration",
    "horde_sdk.worker.generations.ImageSingleGeneration",
    "horde_sdk.worker.generations.TextSingleGeneration",
    "horde_sdk.worker.generations_base.HordeSingleGeneration",
    "horde_sdk.worker.job_base.HordeWorkerJob",
    "horde_sdk.worker.job_base.HordeWorkerJobConfig",
    "horde_sdk.worker.jobs.AlchemyWorkerJob",
    "horde_sdk.worker.jobs.ImageWorkerJob",
    "horde_sdk.worker.jobs.TextWorkerJob",
)

GENERATED_BEGIN = "<!-- BEGIN GENERATED: endpoint-map (build_docs.py) -->"
GENERATED_END = "<!-- END GENERATED: endpoint-map -->"


@dataclass(frozen=True, order=True)
class EndpointRow:
    """One request-to-response relationship rendered in the endpoint map."""

    endpoint: str
    method: str
    request_name: str
    request_path: str
    status: int
    response_name: str
    response_path: str


def namespace_for(path: Path, project_root: Path = PROJECT_ROOT) -> str:
    """Return a Python namespace for a module path below ``project_root``."""
    return path.relative_to(project_root).with_suffix("").as_posix().replace("/", ".")


def module_is_included(namespace: str) -> bool:
    """Return whether a module is part of the published public-plus-advanced corpus."""
    if namespace in EXCLUDED_MODULES:
        return False
    return namespace in INCLUDED_ROOT_MODULES or namespace.startswith(INCLUDED_PREFIXES)


def included_modules(code_root: Path = CODE_ROOT, project_root: Path = PROJECT_ROOT) -> list[tuple[Path, str]]:
    """Return included non-package modules in stable namespace order."""
    modules: list[tuple[Path, str]] = []
    for path in code_root.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        namespace = namespace_for(path, project_root)
        if module_is_included(namespace):
            modules.append((path, namespace))
    return sorted(modules, key=lambda item: item[1])


def public_definitions(path: Path) -> list[str]:
    """Return public classes and functions declared directly in a source module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    ]


def front_matter(title: str, summary: str) -> str:
    """Render front matter shared by generated API pages."""
    return f'---\ntitle: "{title}"\nsummary: "{summary}"\n---\n\n'


def render_module_page(path: Path, namespace: str, expanded: set[str]) -> str:
    """Render one module page with facade objects omitted for their dedicated pages."""
    expanded_names = {object_path.rsplit(".", 1)[1] for object_path in expanded}
    members = [name for name in public_definitions(path) if name not in expanded_names]
    options = ["      inherited_members: false", "      members_order: source"]
    if expanded_names:
        if members:
            options.append("      members:")
            options.extend(f"        - {member}" for member in members)
        else:
            options.append("      members: false")
    return (
        front_matter(namespace, f"Generated Python API reference for {namespace}.")
        + f"# `{namespace}`\n\n"
        + f"::: {namespace}\n    options:\n"
        + "\n".join(options)
        + "\n"
    )


def render_object_page(object_path: str) -> str:
    """Render one facade-object page with inherited public members expanded."""
    name = object_path.rsplit(".", 1)[1]
    return (
        front_matter(name, f"Complete API reference for {object_path}, including inherited members.")
        + f"# `{name}`\n\n"
        + f"::: {object_path}\n"
        + "    options:\n"
        + "      inherited_members: true\n"
        + "      members_order: source\n"
    )


def output_path_for_module(namespace: str, api_docs_root: Path = API_DOCS_ROOT) -> Path:
    """Return the generated Markdown path for a module namespace."""
    relative = namespace.removeprefix("horde_sdk.").replace(".", "/")
    return api_docs_root / f"{relative}.md"


def render_api_index(namespaces: list[str]) -> str:
    """Render the single navigation gateway into the generated API corpus."""
    groups: dict[str, list[str]] = {}
    for namespace in namespaces:
        area = namespace.split(".", 2)[1] if namespace.count(".") >= 2 else "core"
        groups.setdefault(area, []).append(namespace)

    lines = [
        "# Python API index",
        "",
        "The generated reference covers public SDK modules and advanced extension surfaces. Private reflection,",
        "telemetry, scripts, and generated version modules are intentionally excluded.",
        "",
        "Facade classes have dedicated complete pages with inherited members. Other pages show members declared by",
        "their module or class, which keeps model reference pages compact.",
    ]
    for area, area_namespaces in sorted(groups.items()):
        lines += ["", f"## {area.replace('_', ' ').title()}", ""]
        for namespace in area_namespaces:
            target = namespace.removeprefix("horde_sdk.").replace(".", "/") + ".md"
            lines.append(f"- [`{namespace}`]({target})")
    lines.append("")
    return "\n".join(lines)


def expected_api_pages(
    code_root: Path = CODE_ROOT,
    project_root: Path = PROJECT_ROOT,
    api_docs_root: Path = API_DOCS_ROOT,
    expanded_objects: tuple[str, ...] = EXPANDED_OBJECTS,
) -> dict[Path, str]:
    """Build the complete desired generated API tree in memory."""
    pages: dict[Path, str] = {}
    expanded_by_module: dict[str, set[str]] = {}
    for object_path in expanded_objects:
        module, _, _name = object_path.rpartition(".")
        expanded_by_module.setdefault(module, set()).add(object_path)

    namespaces: set[str] = set()
    for source_path, namespace in included_modules(code_root, project_root):
        namespaces.add(namespace)
        expanded = expanded_by_module.get(namespace, set())
        module_path = output_path_for_module(namespace, api_docs_root)
        pages[module_path] = render_module_page(source_path, namespace, expanded)
        for object_path in sorted(expanded):
            object_name = object_path.rsplit(".", 1)[1]
            pages[module_path.with_suffix("") / f"{object_name}.md"] = render_object_page(object_path)

    missing_modules = sorted(set(expanded_by_module) - namespaces)
    if missing_modules:
        raise RuntimeError(f"Expanded API objects refer to excluded or missing modules: {', '.join(missing_modules)}")
    pages[api_docs_root / "README.md"] = render_api_index(sorted(namespaces))
    return pages


def qualified_name(value: type[object]) -> str:
    """Return the fully qualified name of a class."""
    return f"{value.__module__}.{value.__name__}"


def collect_endpoint_rows(request_types: list[type[HordeRequest]]) -> list[EndpointRow]:
    """Collect method-specific endpoint rows directly from SDK request metadata."""
    rows: list[EndpointRow] = []
    for request_type in request_types:
        request_path = qualified_name(request_type)
        for status, response_type in request_type.get_success_status_response_pairs().items():
            rows.append(
                EndpointRow(
                    endpoint=str(request_type.get_api_endpoint_subpath()),
                    method=str(request_type.get_http_method().value),
                    request_name=request_type.__name__,
                    request_path=request_path,
                    status=int(status),
                    response_name=response_type.__name__,
                    response_path=qualified_name(response_type),
                ),
            )
    return sorted(rows)


def discover_request_types() -> list[type[HordeRequest]]:
    """Import the AI Horde model package and return its concrete request classes."""
    package = importlib.import_module("horde_sdk.ai_horde_api.apimodels")
    from horde_sdk.generic_api.apimodels import HordeRequest

    return [
        value
        for _name, value in inspect.getmembers(package, inspect.isclass)
        if issubclass(value, HordeRequest) and not inspect.isabstract(value)
    ]


def render_endpoint_rows(rows: list[EndpointRow]) -> str:
    """Render endpoint rows as a method-specific Markdown table."""
    lines = [
        "| Endpoint | Method | Request type | Success | Response type |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.endpoint}` | `{row.method}` | [{row.request_name}][{row.request_path}] | "
            f"{row.status} | [{row.response_name}][{row.response_path}] |",
        )
    return "\n".join(lines) + "\n"


def render_endpoint_page(path: Path = ENDPOINT_MAP_PATH) -> str:
    """Return the endpoint page with its generated table refreshed."""
    text = path.read_text(encoding="utf-8")
    if GENERATED_BEGIN not in text or GENERATED_END not in text:
        raise RuntimeError(f"{path} is missing endpoint-map generation markers")
    before, remainder = text.split(GENERATED_BEGIN, 1)
    _old, after = remainder.split(GENERATED_END, 1)
    table = render_endpoint_rows(collect_endpoint_rows(discover_request_types()))
    return f"{before}{GENERATED_BEGIN}\n{table}{GENERATED_END}{after}"


def generated_differences(expected: dict[Path, str], api_docs_root: Path = API_DOCS_ROOT) -> list[str]:
    """Return missing, stale, and unexpected generated page descriptions."""
    differences: list[str] = []
    actual_paths = set(api_docs_root.rglob("*.md")) if api_docs_root.exists() else set()
    expected_paths = set(expected)
    for path in sorted(expected_paths - actual_paths):
        differences.append(f"missing generated page: {path.relative_to(PROJECT_ROOT)}")
    for path in sorted(actual_paths - expected_paths):
        differences.append(f"unexpected generated page: {path.relative_to(PROJECT_ROOT)}")
    for path in sorted(actual_paths & expected_paths):
        if path.read_text(encoding="utf-8") != expected[path]:
            differences.append(f"stale generated page: {path.relative_to(PROJECT_ROOT)}")
    return differences


def generate() -> None:
    """Write the complete tracked generated documentation set."""
    expected = expected_api_pages()
    API_DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    actual_paths = set(API_DOCS_ROOT.rglob("*.md"))
    for path in sorted(actual_paths - set(expected)):
        path.unlink()
    for path, content in sorted(expected.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    ENDPOINT_MAP_PATH.write_text(render_endpoint_page(), encoding="utf-8", newline="\n")
    print(f"Generated {len(expected)} API pages and the endpoint map")


def check() -> int:
    """Return nonzero when tracked generated documentation has drifted."""
    expected = expected_api_pages()
    differences = generated_differences(expected)
    if ENDPOINT_MAP_PATH.exists() and ENDPOINT_MAP_PATH.read_text(encoding="utf-8") != render_endpoint_page():
        differences.append(f"stale generated endpoint map: {ENDPOINT_MAP_PATH.relative_to(PROJECT_ROOT)}")
    elif not ENDPOINT_MAP_PATH.exists():
        differences.append(f"missing generated endpoint map: {ENDPOINT_MAP_PATH.relative_to(PROJECT_ROOT)}")
    if differences:
        print("\n".join(differences), file=sys.stderr)
        print("Regenerate with: python docs/build_docs.py generate", file=sys.stderr)
        return 1
    print(f"Generated documentation is current ({len(expected)} API pages)")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the generator or its no-write drift check."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", nargs="?", choices=("generate", "check"), default="generate")
    parser.add_argument("--check", action="store_true", help="Alias for the check command")
    args = parser.parse_args(argv)
    if args.check or args.command == "check":
        return check()
    generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
