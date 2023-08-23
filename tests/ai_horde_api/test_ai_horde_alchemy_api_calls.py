import pytest

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIClientSession
from horde_sdk.ai_horde_api.apimodels.alchemy._async import (
    AlchemyAsyncRequest,
    AlchemyAsyncRequestFormItem,
    AlchemyAsyncResponse,
)
from horde_sdk.ai_horde_api.consts import KNOWN_ALCHEMY_TYPES


class HordeTestException(Exception):
    pass


def test_alchemy_request_cleanup(ai_horde_api_key: str, default_testing_image_base64: str) -> None:
    """Tests that the Alchemy request model works as expected."""
    request = AlchemyAsyncRequest(
        apikey=ai_horde_api_key,
        forms=[
            AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.strip_background),
            AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.caption),
            AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.interrogation),
            AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.nsfw),
            AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus),
        ],
        source_image=default_testing_image_base64,
    )

    with pytest.raises(HordeTestException), AIHordeAPIClientSession() as session:
        response = session.submit_request(request, expected_response_type=AlchemyAsyncResponse)

        assert isinstance(response, AlchemyAsyncResponse)
        raise HordeTestException("This tests that the cleanup request is sent.")


def test_alchemy_request_strip_background(ai_horde_api_key: str, woman_headshot_testing_image_base64: str) -> None:
    AlchemyAsyncRequest(
        apikey=ai_horde_api_key,
        forms=[AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.strip_background)],
        source_image=woman_headshot_testing_image_base64,
    )
