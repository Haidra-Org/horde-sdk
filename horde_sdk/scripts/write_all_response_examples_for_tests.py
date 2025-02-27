"""Write all example responses to a file in the tests/test_data directory."""

import json
from pathlib import Path

from loguru import logger

from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.generic_api.utils.swagger import SwaggerParser


def write_all_example_responses(*, test_data_path: Path | None = None) -> None:
    """Write all example responses to a file in the test_data directory."""
    ai_horde_swagger_doc = SwaggerParser(
        swagger_doc_url=get_ai_horde_swagger_url(),
    ).get_swagger_doc()
    if not test_data_path:
        test_data_path = (
            Path(__file__).parent.parent.parent / "tests" / "test_data" / "ai_horde_api" / "example_responses"
        )
    ai_horde_swagger_doc.write_all_response_examples_to_file(test_data_path)

    files_to_make_arrays = [
        "_v2_users_get_200.json",
    ]
    # Compatibility hacks:

    for file_name in files_to_make_arrays:
        if not (test_data_path / file_name).exists():
            logger.warning(f"File {file_name} does not exist, skipping compatibility hack.")
            continue

        file_contents: str | None = None
        with open(test_data_path / file_name) as f:
            file_contents = f.read()

        if file_contents is None:
            logger.warning(f"File {file_name} is empty, skipping compatibility hack.")
            continue

        if not file_contents.startswith("["):
            logger.warning(
                f"The {file_name} file is not an array, converting it to one to make it compatible with the tests. "
                f"This is a compatibility hack due to the API docs not being correct.",
            )
            file_contents = f"[{file_contents}]"
            file_contents = json.loads(file_contents)

            with open(test_data_path / file_name, "w") as f:
                json.dump(file_contents, f, indent=4)
                f.write("\n")
        else:
            logger.info(f"The {file_name} file is already compatible with the tests.")
            logger.info("This script should be updated to remove this compatibility hack.")

    files_to_make_objects = [
        "_v2_filters_filter_id_get_200.json",
    ]

    # Compatibility hacks:
    for file_name in files_to_make_objects:
        if not (test_data_path / file_name).exists():
            logger.warning(f"File {file_name} does not exist, skipping compatibility hack.")
            continue

        file_contents_object: str | None = None
        with open(test_data_path / file_name) as f:
            file_contents_object = f.read()

        if file_contents_object is None:
            logger.warning(f"File {file_name} is empty, skipping compatibility hack.")
            continue

        if file_contents_object.startswith("["):
            logger.warning(
                f"The {file_name} file is an array, converting it to an object to make it compatible with the tests. "
                f"This is a compatibility hack due to the API docs not being correct.",
            )
            file_contents_object = file_contents_object.strip().strip("[]").strip()
            file_contents_object = json.loads(file_contents_object)

            with open(test_data_path / file_name, "w") as f:
                json.dump(file_contents_object, f, indent=4)
                f.write("\n")

        else:
            logger.info(f"The {file_name} file is already compatible with the tests.")
            logger.info("This script should be updated to remove this compatibility hack.")


if __name__ == "__main__":
    write_all_example_responses()
