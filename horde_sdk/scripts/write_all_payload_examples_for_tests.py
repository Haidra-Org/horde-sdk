"""Write all example payloads to a file in the tests/test_data directory."""

from pathlib import Path

from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.generic_api.utils.swagger import SwaggerParser


def write_example_payloads(*, test_data_path: Path | None = None) -> None:
    """Write all example payloads to a file in the test_data directory."""
    ai_horde_swagger_doc = SwaggerParser(
        swagger_doc_url=get_ai_horde_swagger_url(),
    ).get_swagger_doc()
    if not test_data_path:
        test_data_path = (
            Path(__file__).parent.parent.parent / "tests" / "test_data" / "ai_horde_api" / "example_payloads"
        )
    ai_horde_swagger_doc.write_all_payload_examples_to_file(test_data_path)


if __name__ == "__main__":
    write_example_payloads()
