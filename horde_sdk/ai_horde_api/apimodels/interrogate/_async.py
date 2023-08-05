from horde_sdk.ai_horde_api.apimodels.base import (
    JobResponseMixin,
)
from horde_sdk.generic_api.apimodels import (
    BaseResponse,
    ResponseNeedingFollowUpMixin,
)


class AlchemyAsyncResponse(BaseResponse, JobResponseMixin, ResponseNeedingFollowUpMixin):
    """Represents the data returned from the `/v2/alchemy/async` endpoint.

    v2 API Model: `RequestInterrogationResponse`
    """
