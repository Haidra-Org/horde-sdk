from loguru import logger
from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.alchemy._submit import AlchemyJobSubmitRequest
from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    JobRequestMixin,
)
from horde_sdk.ai_horde_api.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObject,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


# FIXME
class AlchemyFormPayloadStable(HordeAPIObject):
    """Currently unsupported.

    v2 API Model: `ModelInterrogationFormPayloadStable`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ModelInterrogationFormPayloadStable"

    additionalProp1: str = Field(validation_alias="additionalProp1", description="Currently unsupported")
    additionalProp2: str = Field(validation_alias="additionalProp2", description="Currently unsupported")
    additionalProp3: str = Field(validation_alias="additionalProp3", description="Currently unsupported")


class AlchemyPopFormPayload(HordeAPIObject, JobRequestMixin):
    """v2 API Model: `InterrogationPopFormPayload`."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationPopFormPayload"

    form: KNOWN_ALCHEMY_TYPES = Field(
        None,
        description="The name of this interrogation form",
        examples=["caption"],
    )
    payload: AlchemyFormPayloadStable | None = None
    r2_upload: str | None = Field(None, description="The URL in which the post-processed image can be uploaded.")
    source_image: str | None = Field(None, description="The URL From which the source image can be downloaded.")


class NoValidAlchemyFound(HordeAPIObject):
    """v2 API Model: `NoValidInterrogationsFoundStable`."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "NoValidInterrogationsFoundStable"

    bridge_version: int | None = Field(
        None,
        description=(
            "How many waiting requests were skipped because they require a higher version of the bridge than this"
            " worker is running (upgrade if you see this in your skipped list)."
        ),
        examples=[0],
        ge=0,
    )
    untrusted: int | None = Field(
        None,
        description=(
            "How many waiting requests were skipped because they demanded a trusted worker which this worker is not."
        ),
        ge=0,
    )
    worker_id: int | None = Field(
        None,
        description="How many waiting requests were skipped because they demanded a specific worker.",
        ge=0,
    )


class AlchemyPopResponse(HordeResponseBaseModel, ResponseRequiringFollowUpMixin):
    """v2 API Model: `InterrogationPopPayload`."""

    # and not actually specifying a schema
    forms: list[AlchemyPopFormPayload] | None = None
    skipped: NoValidAlchemyFound | None = None

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationPopPayload"

    @override
    @classmethod
    def get_follow_up_default_request_type(cls) -> type[AlchemyJobSubmitRequest]:
        return AlchemyJobSubmitRequest

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[AlchemyJobSubmitRequest]:
        return AlchemyJobSubmitRequest

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if not self.forms:
            return []
        all_ids: list[dict[str, object]] = []
        for form in self.forms:
            if not isinstance(form, AlchemyPopFormPayload):
                logger.warning(f"Skipping form {form} as it is not an AlchemyPopFormPayload")
                continue
            if form.id_:
                if as_python_field_name:
                    all_ids.append({"id_": form.id_})
                else:
                    all_ids.append({"id": form.id_})

        return all_ids

    @override
    @classmethod
    def get_follow_up_request_types(cls) -> list[type[AlchemyJobSubmitRequest]]:  # type: ignore[override]
        """Return a list of all the possible follow up request types for this response."""
        return [AlchemyJobSubmitRequest]


class AlchemyPopRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Represents the data needed to make a request to the `/v2/interrogate/pop` endpoint.

    v2 API Model: `InterrogationPopInput`
    """

    name: str
    priority_usernames: list[str]
    forms: list[KNOWN_ALCHEMY_TYPES]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationPopInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_pop

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyPopResponse]:
        return AlchemyPopResponse
