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
    AIHordePayloadValidationError,
    AIHordeRequestError,
    AIHordeServerException,
)
from horde_sdk.ai_horde_api.fields import GenerationID, ImageID, TeamID, WorkerID
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_FORMS
from horde_sdk.generation_parameters.image.consts import KNOWN_SAMPLERS, KNOWN_SOURCE_PROCESSING
from horde_sdk.worker.consts import WORKER_TYPE

__all__ = [
    "AIHordeAPIManualClient",
    "AIHordeAPIClientSession",
    "AIHordeAPIAsyncManualClient",
    "AIHordeAPIAsyncClientSession",
    "AIHordeAPISimpleClient",
    "AIHordeAPIAsyncSimpleClient",
    "download_image_from_generation",
    "GENERATION_MAX_LIFE",
    "AI_HORDE_BASE_URL",
    "AI_HORDE_API_ENDPOINT_SUBPATH",
    "KNOWN_ALCHEMY_FORMS",
    "GENERATION_STATE",
    "KNOWN_SAMPLERS",
    "KNOWN_SOURCE_PROCESSING",
    "WORKER_TYPE",
    "AIHordeRequestError",
    "AIHordeImageValidationError",
    "AIHordeGenerationTimedOutError",
    "AIHordeServerException",
    "AIHordePayloadValidationError",
    "ImageID",
    "GenerationID",
    "TeamID",
    "WorkerID",
]
