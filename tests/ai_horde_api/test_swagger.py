from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.generic_api.utils.swagger import SwaggerDoc, SwaggerParser


def test_swagger_parser_init():
    SwaggerParser(get_ai_horde_swagger_url())


def test_get_swagger_doc():
    parser = SwaggerParser(get_ai_horde_swagger_url())
    doc = parser.get_swagger_doc()
    assert isinstance(doc, SwaggerDoc)
    assert doc.swagger == "2.0"
    assert doc.basePath == "/api"
    assert doc.info.title == "AI Horde"

    assert doc.produces
    assert "application/json" in doc.produces
    assert doc.consumes
    assert "application/json" in doc.consumes

    assert doc.paths
    assert len(doc.paths) > 0
    assert "/v2/generate/async" in doc.paths

    assert doc.definitions
    assert len(doc.definitions) > 0
    assert "ModelGenerationInputStable" in doc.definitions

    assert doc.responses
    assert len(doc.responses) > 0


def test_extract_all_payload_examples() -> None:
    swagger_doc = SwaggerParser(get_ai_horde_swagger_url()).get_swagger_doc()

    all_request_examples = swagger_doc.extract_all_payload_examples()
    assert len(all_request_examples) > 0, "Failed to extract any examples from the swagger doc"


def test_extract_all_response_examples() -> None:
    swagger_doc = SwaggerParser(get_ai_horde_swagger_url()).get_swagger_doc()

    all_response_examples = swagger_doc.extract_all_response_examples()
    assert len(all_response_examples) > 0, "Failed to extract any examples from the swagger doc"
