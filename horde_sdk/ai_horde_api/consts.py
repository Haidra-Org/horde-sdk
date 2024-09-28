"""AI-Horde specific constants, including enums defined on the API."""

from enum import auto

from strenum import StrEnum

GENERATION_MAX_LIFE = (60 * 20) - 30
"""The maximum time for the life of a generation request in seconds, minus 30 seconds to account for network latency.

This is the amount of time that passes before the server will delete the request.
"""


class GENERATION_STATE(StrEnum):
    """The generation states that are known to the API.

    (ok, censored, faulted, etc...)
    """

    _NONE = ""  # FIXME

    ok = auto()
    """The generation was successful. It still may have encountered warnings."""
    censored = auto()
    """The generation was censored."""
    faulted = auto()
    """The generation encountered an error and was cancelled. It usually is retried automatically."""
    csam = auto()
    """The generation was flagged as CSAM and automatically censored."""
    waiting = auto()
    """The generation is waiting for a worker to be assigned."""
    processing = auto()
    """The generation is being processed by a worker."""
    partial = auto()
    """The generation was returned partially complete."""
    cancelled = auto()
    """The generation was cancelled by the user."""
    done = auto()


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


class ALCHEMY_FORMS(StrEnum):
    """Forms (type of services) for alchemist type workers.

    (nsfw, caption, interrogation, post_process, etc...)
    """

    nsfw = auto()
    caption = auto()
    """Captioning (i.e., BLIP)."""
    interrogation = auto()
    """Interrogation (i.e., CLIP)."""
    post_process = auto()
    """Upscaling, facefixing, etc."""


class KNOWN_SAMPLERS(StrEnum):
    """The samplers that are known to the API.

    (k_lms, k_heun, DDIM, etc)
    """

    k_lms = auto()
    k_heun = auto()
    k_euler = auto()
    k_euler_a = auto()
    k_dpm_2 = auto()
    k_dpm_2_a = auto()
    k_dpm_fast = auto()
    k_dpm_adaptive = auto()
    k_dpmpp_2s_a = auto()
    k_dpmpp_2m = auto()
    dpmsolver = auto()
    k_dpmpp_sde = auto()
    lcm = auto()
    DDIM = "DDIM"


class KNOWN_CONTROLNETS(StrEnum):
    """The controlnets that are known to the API."""

    canny = auto()
    hed = auto()
    depth = auto()
    normal = auto()
    openpose = auto()
    seg = auto()
    scribble = auto()
    fakescribbles = auto()
    hough = auto()


class KNOWN_WORKFLOWS(StrEnum):
    """The controlnets that are known to the API."""

    qr_code = auto()


class KNOWN_SOURCE_PROCESSING(StrEnum):
    """The source processing methods that are known to the API.

    (txt2img, img2img, inpainting, etc)
    """

    txt2img = auto()
    img2img = auto()
    inpainting = auto()
    outpainting = auto()
    remix = auto()
    """Stable Cascade Remix"""


class KNOWN_UPSCALERS(StrEnum):
    """The upscalers that are known to the API.

    (RealESRGAN_x4plus, RealESRGAN_x2plus, RealESRGAN_x4plus_anime_6B, etc)
    """

    RealESRGAN_x4plus = auto()
    RealESRGAN_x2plus = auto()
    RealESRGAN_x4plus_anime_6B = auto()
    NMKD_Siax = auto()
    four_4x_AnimeSharp = "4x_AnimeSharp"
    """AKA 4x_AnimeSharp"""


class KNOWN_FACEFIXERS(StrEnum):
    """The facefixers that are known to the API.

    (CodeFormers, etc)
    """

    GFPGAN = auto()
    CodeFormers = auto()


class KNOWN_MISC_POST_PROCESSORS(StrEnum):
    """The misc post processors that are known to the API.

    (strip_background, etc)
    """

    strip_background = auto()


_all_valid_post_processors_names_and_values = (
    list(KNOWN_UPSCALERS.__members__.keys())
    + list(KNOWN_UPSCALERS.__members__.values())
    + list(KNOWN_FACEFIXERS.__members__.keys())
    + list(KNOWN_FACEFIXERS.__members__.values())
    + list(KNOWN_MISC_POST_PROCESSORS.__members__.keys())
    + list(KNOWN_MISC_POST_PROCESSORS.__members__.values())
)
"""Used to validate post processor names and values. \
    This is because some post processor names are not valid python variable names."""


class POST_PROCESSOR_ORDER_TYPE(StrEnum):
    """The post processor order types that are known to the API.

    (facefixers_first, upscalers_first, custom, etc)
    """

    facefixers_first = auto()
    """The facefixers are processed first."""
    upscalers_first = auto()
    """The upscalers are processed first."""
    custom = auto()
    """User specified post processor order."""


DEFAULT_POST_PROCESSOR_ORDER = POST_PROCESSOR_ORDER_TYPE.facefixers_first
"""The default post processor order."""


class KNOWN_CLIP_BLIP_TYPES(StrEnum):
    """The CLIP and BLIP models that are known to the API."""

    caption = auto()
    """The caption (BLIP) model."""
    interrogation = auto()
    """The interrogation (CLIP) model."""
    nsfw = auto()
    """The NSFW model."""


class KNOWN_INTERROGATORS(StrEnum):
    """The interrogators that are known to the API."""

    vit_l_14 = "ViT-L/14"


class KNOWN_ALCHEMY_TYPES(StrEnum):
    """The alchemy processes (types) that are known to the API.

    (caption, GFPGAN, strip_background, etc)
    """

    _NONE = ""  # FIXME

    caption = KNOWN_CLIP_BLIP_TYPES.caption
    interrogation = KNOWN_CLIP_BLIP_TYPES.interrogation
    nsfw = KNOWN_CLIP_BLIP_TYPES.nsfw

    RealESRGAN_x4plus = KNOWN_UPSCALERS.RealESRGAN_x4plus
    RealESRGAN_x2plus = KNOWN_UPSCALERS.RealESRGAN_x2plus
    RealESRGAN_x4plus_anime_6B = KNOWN_UPSCALERS.RealESRGAN_x4plus_anime_6B
    NMKD_Siax = KNOWN_UPSCALERS.NMKD_Siax
    fourx_AnimeSharp = KNOWN_UPSCALERS.four_4x_AnimeSharp

    GFPGAN = KNOWN_FACEFIXERS.GFPGAN
    CodeFormers = KNOWN_FACEFIXERS.GFPGAN

    strip_background = KNOWN_MISC_POST_PROCESSORS.strip_background


class METADATA_TYPE(StrEnum):
    """The generation metadata types that are known to the API.

    (lora, ti, censorship, etc)
    """

    lora = auto()
    """This refers to a LORA metadata type."""
    ti = auto()
    """This refers to a Textual Inversion metadata type."""
    censorship = auto()
    """The censorship metadata type."""
    source_image = auto()
    """The source image for img2img, inpainting, outpainting, or other source image processing."""
    source_mask = auto()
    """The mask for img2img, inpainting, outpainting, or other source image processing."""
    extra_source_images = auto()
    """Extra source images for the request."""
    batch_index = auto()
    """The index of the batch in a batch request."""
    information = auto()
    """Extra information about the image."""


class METADATA_VALUE(StrEnum):
    """The generation metadata values that are known to the API.

    (download_failed, baseline_mismatch, etc)
    """

    download_failed = auto()
    """Something in the request couldn't be downloaded."""
    parse_failed = auto()
    """Something in the request couldn't be parsed."""
    baseline_mismatch = auto()
    """The model targeted wasn't the correct baseline (e.g., SD15 when the request required SDXL)."""
    csam = auto()
    """The generation was flagged as CSAM and automatically censored."""
    nsfw = auto()
    """The generation is not safe for work."""
    see_ref = auto()
    """See the `ref` field for more information."""


class MODEL_STATE(StrEnum):
    """The model states that are known to the API."""

    all = auto()
    """Both known and custom models."""
    known = auto()
    """Known models that appear in the model reference"""
    custom = auto()
    """Custom models."""


class MODEL_TYPE(StrEnum):
    """The model types that are known to the API."""

    text = auto()
    """Text generation models."""
    image = auto()
    """Image generation models."""


class WarningCode(StrEnum):
    """The warning codes that are known to the API."""

    NoAvailableWorker = auto()
    """There are no available workers for the request."""
    ClipSkipMismatch = auto()
    """The clip skip value doesn't match the model's preferred value."""
    StepsTooFew = auto()
    """The number of steps are lower than recommended."""
    StepsTooMany = auto()
    """The number of steps are higher than recommended."""
    CfgScaleMismatch = auto()
    """The scale in the CFG doesn't match the model's preferred scale."""
    CfgScaleTooSmall = auto()
    """The scale in the CFG is too small for the model to handle."""
    CfgScaleTooLarge = auto()
    """The scale in the CFG is too large for the model to handle."""
    SamplerMismatch = auto()
    """The sampler specified doesn't match the model's preferred sampler."""
    SchedulerMismatch = auto()
    """The scheduler specified doesn't match the model's preferred scheduler."""


class RC(StrEnum):
    """The return codes (typically errors, sometimes warnings) that are known to the API."""

    MissingPrompt = auto()
    """The prompt is missing but is required."""
    CorruptPrompt = auto()
    """The prompt couldn't be parsed."""
    KudosValidationError = auto()
    """The number of kudos for the requesting user is too low."""
    NoValidActions = auto()
    InvalidSize = auto()
    InvalidPromptSize = auto()
    """The prompt is too short or too long."""
    TooManySteps = auto()
    """The number of steps too high to be reasonable."""
    Profanity = auto()
    ProfaneWorkerName = auto()
    """The worker name contains profanity or rude language."""
    ProfaneBridgeAgent = auto()
    """The bridge agent contains profanity or rude language."""
    ProfaneWorkerInfo = auto()
    """The worker info contains profanity or rude language."""
    ProfaneUserName = auto()
    """The user name contains profanity or rude language."""
    ProfaneUserContact = auto()
    """The user contact contains profanity or rude language."""
    ProfaneAdminComment = auto()
    """The admin comment contains profanity or rude language."""
    ProfaneTeamName = auto()
    """The team name contains profanity or rude language."""
    ProfaneTeamInfo = auto()
    """The team info contains profanity or rude language."""
    TooLong = auto()
    TooLongWorkerName = auto()
    """The worker name is too long."""
    TooLongUserName = auto()
    """The user name is too long."""
    NameAlreadyExists = auto()
    """The name is already in use."""
    WorkerNameAlreadyExists = auto()
    """The worker name is already in use."""
    TeamNameAlreadyExists = auto()
    """The team name is already in use."""
    PolymorphicNameConflict = auto()
    """The name conflicts with a polymorphic name in the database."""
    ImageValidationFailed = auto()
    """The image couldn't be parsed. This may be due to a corrupt image."""
    SourceImageResolutionExceeded = auto()
    SourceImageSizeExceeded = auto()
    SourceImageUrlInvalid = auto()
    """The source image URL is invalid or is not accessible."""
    SourceImageUnreadable = auto()
    InpaintingMissingMask = auto()
    """Inpainting was selected but no mask was provided."""
    SourceMaskUnnecessary = auto()
    UnsupportedSampler = auto()
    UnsupportedModel = auto()
    ControlNetUnsupported = auto()
    ControlNetSourceMissing = auto()
    ControlNetInvalidPayload = auto()
    SourceImageRequiredForModel = auto()
    """The model requires a source image."""
    UnexpectedModelName = auto()
    """The model name is unexpected or unknown."""
    TooManyUpscalers = auto()
    """The number of upscalers in the request is too high."""
    ProcGenNotFound = auto()
    InvalidAestheticAttempt = auto()
    AestheticsNotCompleted = auto()
    AestheticsNotPublic = auto()
    AestheticsDuplicate = auto()
    AestheticsMissing = auto()
    AestheticsSolo = auto()
    AestheticsConfused = auto()
    AestheticsAlreadyExist = auto()
    AestheticsServerRejected = auto()
    AestheticsServerError = auto()
    AestheticsServerDown = auto()
    AestheticsServerTimeout = auto()
    InvalidAPIKey = auto()
    """The API key specified is invalid."""
    WrongCredentials = auto()
    """The API key specified doesn't match the target action."""
    NotAdmin = auto()
    """Only admins can perform this action."""
    NotModerator = auto()
    """Only moderators can perform this action."""
    NotOwner = auto()
    NotPrivileged = auto()
    AnonForbidden = auto()
    AnonForbiddenWorker = auto()
    AnonForbiddenUserMod = auto()
    NotTrusted = auto()
    """Only trusted users can perform this action."""
    UntrustedTeamCreation = auto()
    UntrustedUnsafeIP = auto()
    WorkerMaintenance = auto()
    WorkerFlaggedMaintenance = auto()
    TooManySameIPs = auto()
    WorkerInviteOnly = auto()
    UnsafeIP = auto()
    TimeoutIP = auto()
    TooManyNewIPs = auto()
    KudosUpfront = auto()
    """The user must pay kudos upfront. This is typically only for anonymous users surpassing a certain kudos cost for
    their request."""
    SharedKeyEmpty = auto()
    SharedKeyExpired = auto()
    """The shared key has expired."""
    SharedKeyInsufficientKudos = auto()
    """The shared key doesn't have enough kudos to perform this action"""
    InvalidJobID = auto()
    """The job ID was not found, has timed out or has been deleted."""
    RequestNotFound = auto()
    """The request was not found, has timed out or has been deleted."""
    WorkerNotFound = auto()
    """The worker was not found."""
    TeamNotFound = auto()
    """The team was not found."""
    FilterNotFound = auto()
    """The filter was not found."""
    UserNotFound = auto()
    """The user was not found."""
    DuplicateGen = auto()
    AbortedGen = auto()
    RequestExpired = auto()
    TooManyPrompts = auto()
    NoValidWorkers = auto()
    MaintenanceMode = auto()
    TargetAccountFlagged = auto()
    SourceAccountFlagged = auto()
    FaultWhenKudosReceiving = auto()
    FaultWhenKudosSending = auto()
    TooFastKudosTransfers = auto()
    KudosTransferToAnon = auto()
    """The user is trying to transfer kudos to the anonymous user."""
    KudosTransferToSelf = auto()
    """The user is trying to transfer kudos to themselves."""
    KudosTransferNotEnough = auto()
    """The user doesn't have enough kudos to transfer."""
    NegativeKudosTransfer = auto()
    """The user is trying to transfer a negative amount of kudos."""
    KudosTransferFromAnon = auto()
    InvalidAwardUsername = auto()
    KudosAwardToAnon = auto()
    NotAllowedAwards = auto()
    NoWorkerModSelected = auto()
    NoUserModSelected = auto()
    NoHordeModSelected = auto()
    NoTeamModSelected = auto()
    NoFilterModSelected = auto()
    NoSharedKeyModSelected = auto()
    BadRequest = auto()
    Forbidden = auto()
    Locked = auto()
    ControlNetMismatch = auto()
    HiResFixMismatch = auto()
    TooManyLoras = auto()
    """The number of LORAs in the request is too high."""
    BadLoraVersion = auto()
    """The LORA version specficied is not valid."""
    TooManyTIs = auto()
    """The number of TIs in the request is too high."""
    BetaAnonForbidden = auto()
    BetaComparisonFault = auto()
    BadCFGDecimals = auto()
    """The number of decimals in the CFG is invalid."""
    BadCFGNumber = auto()
    """The number in the CFG is invalid."""
    BadClientAgent = auto()
    """The client agent is invalid."""
    SpecialMissingPayload = auto()
    SpecialForbidden = auto()
    SpecialMissingUsername = auto()
    SpecialModelNeedsSpecialUser = auto()
    SpecialFieldNeedsSpecialUser = auto()
    Img2ImgMismatch = auto()
    TilingMismatch = auto()
    EducationCannotSendKudos = auto()
    """The account is an education account and cannot send kudos."""
    InvalidPriorityUsername = auto()
    OnlyServiceAccountProxy = auto()
    """"Only accounts marked as service accounts can use this field."""
    RequiresTrust = auto()
    InvalidRemixModel = auto()
    InvalidExtraSourceImages = auto()
    TooManyExtraSourceImages = auto()
    MissingFullSamplerOrder = auto()
    TooManyStopSequences = auto()
    """The text request has too many stop sequences."""
    ExcessiveStopSequence = auto()
    """The text request has an excessive stop sequence."""
    TokenOverflow = auto()
    MoreThanMinExtraSourceImage = auto()


class PROGRESS_STATE(StrEnum):
    """The state of a request as seen on the server."""

    waiting = auto()
    finished = auto()
    timed_out = auto()
