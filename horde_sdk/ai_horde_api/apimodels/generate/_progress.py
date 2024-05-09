from horde_sdk.generic_api.apimodels import HordeAPIObject, ResponseWithProgressMixin


class ResponseGenerationProgressInfoMixin(HordeAPIObject):
    finished: int
    """The amount of finished jobs in this request."""
    processing: int
    """The amount of still processing jobs in this request."""
    restarted: int
    """The amount of jobs that timed out and had to be restarted or were reported as failed by a worker."""
    waiting: int
    """The amount of jobs waiting to be picked up by a worker."""
    done: bool
    """True when all jobs in this request are done. Else False."""
    faulted: bool = False
    """True when this request caused an internal server error and could not be completed."""
    wait_time: int
    """The expected amount to wait (in seconds) to generate all jobs in this request."""
    queue_position: int
    """The position in the requests queue. This position is determined by relative Kudos amounts."""
    kudos: float
    """The amount of total Kudos this request has consumed until now."""
    is_possible: bool = True
    """If False, this request will not be able to be completed with the pool of workers currently available."""


class ResponseGenerationProgressCombinedMixin(ResponseWithProgressMixin, ResponseGenerationProgressInfoMixin):
    pass
