"""Definitions for the AI Horde API."""

from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIAsyncManualClient,
    AIHordeAPIAsyncSimpleClient,
    AIHordeAPIClientSession,
    AIHordeAPIManualClient,
    AIHordeAPISimpleClient,
    download_image_from_generation,
)
from horde_sdk.ai_horde_api.consts import (
    GENERATION_MAX_LIFE,
    GENERATION_STATE,
)
from horde_sdk.ai_horde_api.endpoints import (
    AI_HORDE_API_ENDPOINT_SUBPATH,
    AI_HORDE_BASE_URL,
)
from horde_sdk.ai_horde_api.exceptions import (
    AIHordeGenerationTimedOutError,
    AIHordeImageValidationError,
    AIHordeRequestError,
    AIHordeServerException,
)
from horde_sdk.ai_horde_api.fields import GenerationID, ImageID, TeamID, WorkerID
from horde_sdk.exceptions import PayloadValidationError
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_FORMS
from horde_sdk.generation_parameters.image.consts import KNOWN_SAMPLERS, KNOWN_SOURCE_PROCESSING

__all__ = [
    "AIHordeAPIAsyncClientSession",
    "AIHordeAPIAsyncManualClient",
    "AIHordeAPIAsyncSimpleClient",
    "AIHordeAPIClientSession",
    "AIHordeAPIManualClient",
    "AIHordeAPISimpleClient",
    "download_image_from_generation",
    "GENERATION_MAX_LIFE",
    "GENERATION_STATE",
    "AI_HORDE_API_ENDPOINT_SUBPATH",
    "AI_HORDE_BASE_URL",
    "AIHordeGenerationTimedOutError",
    "AIHordeImageValidationError",
    "AIHordeRequestError",
    "AIHordeServerException",
    "GenerationID",
    "ImageID",
    "TeamID",
    "WorkerID",
    "PayloadValidationError",
    "KNOWN_ALCHEMY_FORMS",
    "KNOWN_SAMPLERS",
    "KNOWN_SOURCE_PROCESSING",
]
