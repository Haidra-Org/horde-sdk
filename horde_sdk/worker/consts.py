from copy import deepcopy
from enum import auto
from typing import ClassVar

from strenum import StrEnum


class WORKER_ERRORS(StrEnum):
    """The reason a job faulted."""

    UNHANDLED_EXCEPTION = auto()
    """An error not otherwise specified occurred."""
    UNHANDLED_EXCEPTION_FROM_BACKEND = auto()
    """An error was caught originating from within the backend."""
    SYSTEM_OUT_OF_MEMORY = auto()
    """The system ran out of memory."""
    GPU_OUT_OF_MEMORY = auto()
    """The GPU ran out of memory."""
    NETWORK_ISSUE = auto()
    """There was a network issue, such as a timeout or a connection error."""
    SAFEGUARD_TIMEOUT = auto()
    """A reasonable time limit was exceeded, such as a model taking too long to load or generate."""


class GENERATION_PROGRESS(StrEnum):
    """The state of a generation."""

    NOT_STARTED = auto()
    """The generation has not started."""
    ERROR = auto()
    """An error occurred during generation. The most recent step will be retried up to a certain number of times."""
    PRELOADING = auto()
    """The generation is preloading any models to RAM/VRAM. Preloading is skipped if the models are already loaded."""
    PRELOADING_COMPLETE = auto()
    """The generation has completed preloading."""
    GENERATING = auto()
    """The generation is in progress. This will also preload if that step did not yet occur."""
    PENDING_POST_PROCESSING = auto()
    """The generation has completed and is pending post-processing."""
    POST_PROCESSING = auto()
    """The generation is post-processing the generated data."""
    PENDING_SAFETY_CHECK = auto()
    """The generation was created and is pending safety check."""
    SAFETY_CHECKING = auto()
    """The generation is being safety checked."""
    PENDING_SUBMIT = auto()
    """The generation has completed safety check and is pending submission."""
    SUBMITTING = auto()
    """The generation is pending submission."""
    SUBMIT_COMPLETE = auto()
    """The generation has been successfully submitted."""
    ABORTED = auto()
    """The generation has failed because one or more steps failed too many times. An attempt to notify the API will
    be made."""
    REPORTED_FAILED = auto()
    """The generation has been reported as failed to the API."""
    USER_REQUESTED_ABORT = auto()
    """The generation was aborted by the submitting user's request."""
    USER_ABORT_COMPLETE = auto()
    """The generation was aborted (by user's request) and the API has been notified accordingly."""
    ABANDONED = auto()
    """The generation failed and the API could not be notified. It has simply been discarded.

    Note that this can lead to a worker being put into maintenance mode if too many generations are abandoned
    within a certain time frame.
    """


def is_generation_state_failing(progress: GENERATION_PROGRESS) -> bool:
    """Check if the generation is failing."""
    return progress in {
        GENERATION_PROGRESS.ERROR,
        GENERATION_PROGRESS.ABORTED,
        GENERATION_PROGRESS.REPORTED_FAILED,
        GENERATION_PROGRESS.USER_REQUESTED_ABORT,
        GENERATION_PROGRESS.ABANDONED,
    }


initial_generation_state = GENERATION_PROGRESS.NOT_STARTED
# Base transitions dictionary
base_generate_progress_transitions: dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]] = {
    GENERATION_PROGRESS.NOT_STARTED: [
        GENERATION_PROGRESS.PRELOADING,
        GENERATION_PROGRESS.GENERATING,
        GENERATION_PROGRESS.PENDING_POST_PROCESSING,
        GENERATION_PROGRESS.POST_PROCESSING,
    ],
    GENERATION_PROGRESS.PRELOADING: [GENERATION_PROGRESS.PRELOADING_COMPLETE, GENERATION_PROGRESS.ERROR],
    GENERATION_PROGRESS.PRELOADING_COMPLETE: [
        GENERATION_PROGRESS.GENERATING,
        GENERATION_PROGRESS.PENDING_POST_PROCESSING,
        GENERATION_PROGRESS.POST_PROCESSING,
        GENERATION_PROGRESS.ERROR,
    ],
    GENERATION_PROGRESS.GENERATING: [
        GENERATION_PROGRESS.PENDING_POST_PROCESSING,
        GENERATION_PROGRESS.POST_PROCESSING,
        GENERATION_PROGRESS.PENDING_SAFETY_CHECK,
        GENERATION_PROGRESS.SAFETY_CHECKING,
        GENERATION_PROGRESS.ERROR,
    ],
    GENERATION_PROGRESS.PENDING_POST_PROCESSING: [GENERATION_PROGRESS.POST_PROCESSING, GENERATION_PROGRESS.ERROR],
    GENERATION_PROGRESS.POST_PROCESSING: [
        GENERATION_PROGRESS.PENDING_SAFETY_CHECK,
        GENERATION_PROGRESS.SAFETY_CHECKING,
        GENERATION_PROGRESS.ERROR,
    ],
    GENERATION_PROGRESS.PENDING_SAFETY_CHECK: [GENERATION_PROGRESS.SAFETY_CHECKING, GENERATION_PROGRESS.ERROR],
    GENERATION_PROGRESS.SAFETY_CHECKING: [
        GENERATION_PROGRESS.PENDING_SUBMIT,
        GENERATION_PROGRESS.ERROR,
    ],
    GENERATION_PROGRESS.PENDING_SUBMIT: [GENERATION_PROGRESS.SUBMITTING, GENERATION_PROGRESS.ERROR],
    GENERATION_PROGRESS.SUBMITTING: [
        GENERATION_PROGRESS.SUBMIT_COMPLETE,
        GENERATION_PROGRESS.ERROR,
        GENERATION_PROGRESS.ABANDONED,
    ],
    GENERATION_PROGRESS.SUBMIT_COMPLETE: [],
    GENERATION_PROGRESS.ABORTED: [GENERATION_PROGRESS.REPORTED_FAILED, GENERATION_PROGRESS.ERROR],
    GENERATION_PROGRESS.REPORTED_FAILED: [],
    GENERATION_PROGRESS.ERROR: [GENERATION_PROGRESS.ABORTED],
    GENERATION_PROGRESS.USER_REQUESTED_ABORT: [GENERATION_PROGRESS.USER_ABORT_COMPLETE, GENERATION_PROGRESS.ABANDONED],
    GENERATION_PROGRESS.USER_ABORT_COMPLETE: [],
    GENERATION_PROGRESS.ABANDONED: [],
}
"""The default transitions for a generation.

Note to developers: NOT_STARTED must be the first state and ERROR cannot be a valid second state.
You can find a visual aid in `docs/ai-horde-worker/worker_states_flow.md`.
"""
base_generate_progress_transitions_no_safety = deepcopy(base_generate_progress_transitions)
base_generate_progress_transitions_no_safety[GENERATION_PROGRESS.GENERATING] = [
    GENERATION_PROGRESS.PENDING_POST_PROCESSING,
    GENERATION_PROGRESS.POST_PROCESSING,
    GENERATION_PROGRESS.PENDING_SUBMIT,
    GENERATION_PROGRESS.SUBMITTING,
    GENERATION_PROGRESS.ERROR,
]

base_generate_progress_transitions_no_safety[GENERATION_PROGRESS.POST_PROCESSING] = [
    GENERATION_PROGRESS.PENDING_SUBMIT,
    GENERATION_PROGRESS.ERROR,
]


# Finalized generation states
finalized_generation_states = {
    GENERATION_PROGRESS.SUBMIT_COMPLETE,
    GENERATION_PROGRESS.REPORTED_FAILED,
    GENERATION_PROGRESS.USER_ABORT_COMPLETE,
    GENERATION_PROGRESS.ABANDONED,
}


# Specific transitions for image generation
default_image_generate_progress_transitions = deepcopy(base_generate_progress_transitions)

# Specific transitions for alchemy
# At the time of writing, alchemy does not perform safety checks
default_alchemy_generate_progress_transitions = deepcopy(base_generate_progress_transitions_no_safety)

# Specific transitions for text generation
# At the time of writing, text generation does not perform safety checks
default_text_generate_progress_transitions = deepcopy(base_generate_progress_transitions_no_safety)


class JobState(StrEnum):
    """The state of a job."""

    QUEUED = auto()
    """The job has been received and is waiting to be processed."""
    PREPARING = auto()
    """The job is being prepared for processing."""
    GENERATING = auto()
    """The job is in the process of generating."""
    PENDING_SAFETY_CHECK = auto()
    """The job was generated and is pending safety check."""
    PENDING_SUBMIT = auto()
    """The job is pending submission."""
    WAITING_ON_NETWORK = auto()
    """The job is waiting on network IO."""
    SUCCESSFULLY_COMPLETED = auto()
    """The job finished successfully."""
    FAULTED = auto()
    """The job faulted. Faulted jobs are ones which failed catastrophically and will not be retried.

    Note: This is different from a generation faulting, which can be submitted as a faulted generation.
    """


class HordeWorkerConfigDefaults:
    """Default values for HordeWorkerJobConfig."""

    DEFAULT_MAX_CONSECUTIVE_FAILED_JOB_SUBMITS: int = 3
    """The default maximum number of consecutive times a job can fail to submit to the API before it is marked as
    faulted. This is used to prevent a job from being retried indefinitely and to prevent a job from being submitted
    well after it would have likely have been marked stale by the API.

    Jobs which are faulted are *abandoned* and no further attempts are made to submit any generations in the job nor to
    notify the API that the job failed.
    """

    DEFAULT_JOB_SUBMIT_RETRY_DELAY: float = 2.0
    """The default delay in seconds between retries to submit a job to the API after submit issues."""

    _UNREASONABLE_MAX_CONSECUTIVE_FAILED_JOB_SUBMITS: int = 10
    """The highest number of consecutive failed job submits allowed in any configuration.

    This is used internally to the sdk as a final safeguard to prevent mistakes in configuration.
    """

    DEFAULT_MAX_GENERATION_FAILURES: int = 3
    """The default maximum number of times a generation can fail before it is abandoned.

    **Note:** *Generations* which fail are reported to the API as failed, but the job itself is not
    necessarily *faulted*. If notifying the API of a failed generation fails the number of times specified by
    `max_consecutive_failed_job_submits`, then the job is marked as faulted and is abandoned.
    """

    _UNREASONABLE_MAX_GENERATION_FAILURES: int = 10
    """The highest number of generation failures allowed in any configuration.

    This is used internally to the sdk as a final safeguard to prevent mistakes in configuration.
    """

    DEFAULT_STATE_ERROR_LIMITS: ClassVar[dict[GENERATION_PROGRESS, int]] = {
        GENERATION_PROGRESS.PRELOADING: 3,
        GENERATION_PROGRESS.GENERATING: 3,
        GENERATION_PROGRESS.SAFETY_CHECKING: 3,
        GENERATION_PROGRESS.SUBMITTING: 10,
        GENERATION_PROGRESS.USER_REQUESTED_ABORT: 10,
    }

    DEFAULT_UPLOAD_TIMEOUT: float = 10.0
    DEFAULT_MAX_RETRIES: int = 10
    DEFAULT_RETRY_DELAY: float = 1.0

    DEFAULT_RESULT_IMAGE_FORMAT: str = "WebP"
    DEFAULT_RESULT_IMAGE_QUALITY: int = 95
    DEFAULT_RESULT_IMAGE_PIL_METHOD: int = 6


class KNOWN_DISPATCH_SOURCE(StrEnum):
    """The known sources of a dispatch."""

    UNKNOWN = auto()
    """The source of the dispatch is unknown."""

    LOCAL_CUSTOM_3RD_PARTY = auto()
    """The source of the dispatch is a local custom 3rd party API."""

    AI_HORDE_API_OFFICIAL = auto()
    """The source of the dispatch is the official AI Horde API."""

    AI_HORDE_API_FORK = auto()
    """The source of the dispatch is a fork of the official AI Horde API."""


class KNOWN_INFERENCE_BACKEND(StrEnum):
    """The known generative inference backends."""

    UNKNOWN = auto()
    """The inference backend is unknown."""

    IN_MODEL_NAME = auto()
    """The model name is prepended with the backend name."""

    CUSTOM_UNPUBLISHED = auto()
    """The inference backend is a custom, unpublished backend."""

    COMFYUI = auto()
    """The inference backend is ComfyUI."""

    A1111 = auto()
    """The inference backend is A1111."""

    HORDE_ALCHEMIST = auto()
    """The inference backend is the Horde Alchemist."""

    KOBOLD_CPP = auto()
    """The inference backend is Kobold CPP."""

    APHRODITE = auto()
    """The inference backend is Aphrodite."""


class KNOWN_ALCHEMY_BACKEND(StrEnum):
    """The known alchemy backends."""

    UNKNOWN = auto()
    """The alchemy backend is unknown."""

    CUSTOM_UNPUBLISHED = auto()
    """The alchemy backend is a custom, unpublished backend."""

    HORDE_ALCHEMIST = auto()
    """The alchemy backend is the Horde Alchemist."""


class REQUESTED_BACKEND_CONSTRAINTS(StrEnum):
    """What constraints on backends to use were requested by the user/server."""

    ANY = auto()
    """Any backend is acceptable."""

    SPECIFIED = auto()
    """Only the specified backend is acceptable."""

    DEFAULT_IMAGE = auto()
    """Only the default image backend is acceptable."""

    DEFAULT_TEXT = auto()
    """Only the default text backend is acceptable."""

    DEFAULT_AUDIO = auto()
    """Only the default audio backend is acceptable."""

    DEFAULT_VIDEO = auto()
    """Only the default video backend is acceptable."""

    DEFAULT_ALCHEMY = auto()
    """Only the default alchemy backend is acceptable."""

    NO_CUSTOM = auto()
    """Only official backends are acceptable."""

    ONLY_CUSTOM = auto()
    """Only custom backends are acceptable."""


class REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE(StrEnum):
    """The choice for what to do when a requested source image couldn't be parsed or is otherwise unusable."""

    TXT2IMG_FALLBACK = auto()
    """Use txt2img instead if the source image is unusable."""

    ABANDON = auto()
    """Abandon the generation if the source image is unusable."""

    USE_WHITE_IMAGE = auto()
    """Use a white image if the source image is unusable."""

    USE_BLACK_IMAGE = auto()
    """Use a black image if the source image is unusable."""

    USE_NOISE_IMAGE = auto()
    """Use a noise image if the source image is unusable."""


class WORKER_TYPE(StrEnum):
    """The worker types that are known to the API.

    (alchemy, image, text, etc...)
    """

    all = ""
    """All worker types."""
    image = auto()
    """Image generation worker."""
    text = auto()
    """Text generation worker."""
    interrogation = auto()
    """Alchemy/Interrogation worker."""
    alchemist = "interrogation"
    """Alchemy/Interrogation worker."""
