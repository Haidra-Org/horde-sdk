from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.generic_api.utils.swagger import SwaggerDoc, SwaggerParser


def test_swagger_parser_init() -> None:
    """Test that the SwaggerParser can be initialized with a swagger doc url."""
    SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url())


def test_get_swagger_doc() -> None:
    """Test that the SwaggerParser can be initialized and that the swagger doc is parsed correctly."""
    parser = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url())
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
    """Test that the payload examples can be extracted from the swagger doc."""
    swagger_doc = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url()).get_swagger_doc()

    all_request_examples = swagger_doc.get_all_payload_examples()
    assert len(all_request_examples) > 0, "Failed to extract any examples from the swagger doc"


def test_extract_all_response_examples() -> None:
    """Test that the response examples can be extracted from the swagger doc."""
    swagger_doc = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url()).get_swagger_doc()

    all_response_examples = swagger_doc.get_all_response_examples()
    assert len(all_response_examples) > 0, "Failed to extract any examples from the swagger doc"
