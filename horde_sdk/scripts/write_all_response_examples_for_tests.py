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

    # Compatibility hacks:
    # `_v2_users_get_200.json` needs to have the object added to an array and overwritten
    with open(test_data_path / "_v2_users_get_200.json") as f:
        _v2_users_get_200 = f.read()

    if not _v2_users_get_200.startswith("["):
        logger.warning(
            "The _v2_users_get_200.json file is not an array, converting it to one to make it compatible with the "
            "tests. This is a compatibility hack due to the API docs not being correct.",
        )
        _v2_users_get_200 = f"[{_v2_users_get_200}]"
        _v2_users_get_200 = json.loads(_v2_users_get_200)

        with open(test_data_path / "_v2_users_get_200.json", "w") as f:
            json.dump(_v2_users_get_200, f, indent=4)
            f.write("\n")
    else:
        logger.info("The _v2_users_get_200.json file is already compatible with the tests.")
        logger.info("This script should be updated to remove this compatibility hack.")


if __name__ == "__main__":
    write_all_example_responses()
