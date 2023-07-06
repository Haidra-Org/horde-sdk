from horde_sdk.ai_horde_api.utils.swagger import SwaggerDoc, SwaggerParser


def test_swagger_parser_init():
    SwaggerParser()


def test_get_swagger_doc():
    parser = SwaggerParser()
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
