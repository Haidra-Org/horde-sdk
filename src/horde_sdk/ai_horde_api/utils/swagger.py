import requests
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL

SWAGGER_DOC_URL = f"{AI_HORDE_BASE_URL}/swagger.json"


class SwaggerParser:
    _swagger_json: dict

    def __init__(self) -> None:
        # Try to get the swagger.json from the server
        try:
            response = requests.get(SWAGGER_DOC_URL)
            response.raise_for_status()
            self._swagger_json = response.json()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Failed to get swagger.json from server: {e.response.text}") from e

    def 