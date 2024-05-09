from __future__ import annotations

from pydantic import Field

from horde_sdk.ai_horde_api.fields import JobID
from horde_sdk.generic_api.apimodels import (
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


class TextGenerateJobPopResponse(
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
    # ResponseRequiringDownloadMixin, # TODO: Implement download for extra source images when api supports it
):
    id_: JobID | None = Field(None, alias="id")
    """The UUID for this image generation."""
