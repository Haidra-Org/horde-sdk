from pathlib import Path

from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.generic_api.utils.swagger import SwaggerParser


def main(*, test_data_path: Path | None = None):
    ai_horde_swagger_doc = SwaggerParser(
        swagger_doc_url=get_ai_horde_swagger_url(),
    ).get_swagger_doc()
    if not test_data_path:
        test_data_path = (
            Path(__file__).parent.parent.parent.parent / "tests" / "test_data" / "ai_horde_api" / "example_payloads"
        )
    ai_horde_swagger_doc.write_all_payload_examples_to_file(test_data_path)


if __name__ == "__main__":
    main()
