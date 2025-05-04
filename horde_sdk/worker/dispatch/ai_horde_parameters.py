"""Contains the implemented classes that encapsulate the parameters for the dispatching of a task to a worker.

This includes meta-parameters that are API-specific (ids), pertain to API expectations (time to live, etc),
or otherwise required for the worker to complete the task (such as r2 upload URLs).
"""

from horde_sdk.ai_horde_api.apimodels import NoValidRequestFound
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.generic_api.apimodels import HordeAPIObjectBaseModel
from horde_sdk.worker.consts import REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE
from horde_sdk.worker.dispatch.base import DispatchParameterBase


class AIHordeDispatchParameters(DispatchParameterBase):
    """Base class for all AI Horde dispatch parameter sets."""

    generation_ids: list[GenerationID]
    """The UUIDs for this generation."""

    no_valid_request_found_reasons: NoValidRequestFound | HordeAPIObjectBaseModel  # FIXME
    """The reasons why no valid request was found for this worker (as in, no job to dispatch to this worker)."""

    source_image_fallback_choice: REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE | str = (
        REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.ABANDON
    )
    """The source image fallback choice to use for this job."""


class AIHordeR2DispatchParameters(AIHordeDispatchParameters):
    """Dispatch parameters for R2 tasks."""

    r2_upload_url_map: dict[GenerationID, str]
    """The map of GenerationID to R2 upload URLs for this job."""
