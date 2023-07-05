from horde_sdk.ai_horde_api.fields import GenerationID, WorkerID
from horde_sdk.generic_api.apimodels import BaseRequestAuthenticated


class BaseImageGenerateJobRequest(BaseRequestAuthenticated):
    id: str | GenerationID  # noqa: A003
    """The UUID for this job."""


class BaseWorkerRequest(BaseRequestAuthenticated):
    worker_id: str | WorkerID
    """The UUID of the worker in question for this request."""
