import json
from pathlib import Path


def dynamically_create_library_markdown_stubs() -> None:
    # Create mkdocs documentation using mkdocstrings
    project_root = Path(__file__).parent.parent
    code_root = Path(__file__).parent.parent / "horde_sdk"

    # Get every .py file in the code_root directory and all subdirectories
    py_files = list(code_root.glob("**/*.py"))

    # Sort the files by path
    sorted_py_files = sorted(py_files, key=lambda x: str(x))

    pyfile_lookup = convert_list_of_paths_to_namespaces(sorted_py_files, project_root)

    # Get all the folders in code_root and its subdirectories
    code_root_paths = list(code_root.glob("**/*"))
    code_root_paths.append(code_root)
    code_root_paths = [path for path in code_root_paths if path.is_dir()]

    folder_lookup = convert_list_of_paths_to_namespaces(code_root_paths, project_root)
    # Remove any files from the folder_lookup

    # For each folder in the folder_lookup, create a file in the docs folder
    for folder, _namespace in folder_lookup.items():
        relative_folder = folder.relative_to(project_root)
        relative_folder = "docs" / relative_folder
        relative_folder.mkdir(parents=True, exist_ok=True)

        with open(relative_folder / ".pages", "w", encoding="utf-8") as f:
            if relative_folder.name == "horde_sdk":
                f.write("title: Horde SDK Code Reference\n")
            else:
                f.write(f"title: {relative_folder.name}\n")

        # Get all the files in the folder
        files_in_folder = list(folder.glob("*.py"))

        # Remove any files that start with a dunderscore
        files_in_folder = [file for file in files_in_folder if "__" not in str(file)]

        # Sort the files by path
        sorted_files_in_folder = sorted(files_in_folder, key=lambda x: str(x))

        if len(sorted_files_in_folder) == 0:
            continue

        for file in sorted_files_in_folder:
            with open(relative_folder / f"{file.stem}.md", "w", encoding="utf-8") as f:
                f.write(f"# {file.stem}\n")
                file_namespace = pyfile_lookup[file]
                f.write(f"::: {file_namespace}\n")


def convert_list_of_paths_to_namespaces(paths: list[Path], root: Path) -> dict[Path, str]:
    # Convert path to string, remove everything in the path before "horde_sdk"
    lookup = {path: str(path).replace(str(root), "") for path in paths}

    # Remove any entry with a dunderscore
    lookup = {key: value for key, value in lookup.items() if "__" not in value}

    # If ends in .py, remove that
    lookup = {key: value[:-3] if value.endswith(".py") else value for key, value in lookup.items()}

    # Replace all slashes with dots
    lookup = {key: value.replace("\\", ".") for key, value in lookup.items()}

    # Unix paths too
    lookup = {key: value.replace("/", ".") for key, value in lookup.items()}

    # Remove the first dot
    lookup = {key: value[1:] if value.startswith(".") else value for key, value in lookup.items()}

    # Purge any empty values
    return {key: value for key, value in lookup.items() if value}


def api_to_sdk_map_create_markdown() -> None:
    api_to_sdk_payload_map: dict[str, dict[str, str]] = {}
    api_to_sdk_response_map: dict[str, dict[str, str]] = {}

    with open("docs/api_to_sdk_payload_map.json") as f:
        api_to_sdk_payload_map = json.load(f)

    with open("docs/api_to_sdk_response_map.json") as f:
        api_to_sdk_response_map = json.load(f)

    # Write the mapping page with the API Endpoint sorted alphabetically
    with open("docs/api_to_sdk_map.md", "w") as f:
        f.write("# AI-Horde API Model to SDK Class Map\n")
        f.write("This is a mapping of the AI-Horde API models (defined at ")
        f.write("[https://stablehorde.net/api/](https://stablehorde.net/api/), see also ")
        f.write("[the swagger doc](https://stablehorde.net/api/swagger.json)) to the SDK classes.\n\n")
        f.write("## Payloads\n")
        f.write("| API Endpoint | HTTP Method | SDK Request Type |\n")
        f.write("| ------------ | ----------- | ---------------- |\n")
        for api_endpoint, http_method_map in sorted(api_to_sdk_payload_map.items()):
            for http_method, sdk_request_type in http_method_map.items():
                f.write(
                    f"| {api_endpoint} | {http_method} | [{sdk_request_type.split('.')[-1]}][{sdk_request_type}] |\n",
                )
        f.write("\n\n")
        f.write("## Responses\n")
        f.write("| API Endpoint | HTTP Status Code | SDK Response Type |\n")
        f.write("| ------------ | ----------- | ----------------- |\n")
        for api_endpoint, http_status_code_map in sorted(api_to_sdk_response_map.items()):
            for http_status_code, _sdk_response_type in http_status_code_map.items():
                f.write(
                    f"| {api_endpoint} | {http_status_code} | "
                    f"[{_sdk_response_type.split('.')[-1]}][{_sdk_response_type}] |\n",
                )


if __name__ == "__main__":
    dynamically_create_library_markdown_stubs()
    api_to_sdk_map_create_markdown()
