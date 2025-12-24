from pydantic import BaseModel


class SafetyResult(BaseModel):
    """A model representing the result of a safety check."""

    is_nsfw: bool
    """Indicates if the content is NSFW (Not Safe For Work)."""

    nsfw_likelihood: float | None = None
    """A float representing the likelihood that the content is NSFW, typically between 0.0 and 1.0."""

    is_csam: bool | None = None
    """Indicates if the content is CSAM."""

    csam_likelihood: float | None = None
    """A float representing the likelihood that the content is CSAM, typically between 0.0 and 1.0."""

    is_hate_speech: bool | None = None
    """Indicates if the content is hate speech."""

    hate_speech_likelihood: float | None = None
    """A float representing the likelihood that the content is hate speech, typically between 0.0 and 1.0."""

    is_violent: bool | None = None
    """Indicates if the content is violent."""

    violent_likelihood: float | None = None
    """A float representing the likelihood that the content is violent, typically between 0.0 and 1.0."""

    is_self_harm: bool | None = None
    """Indicates if the content promotes self-harm."""

    self_harm_likelihood: float | None = None
    """A float representing the likelihood that the content promotes self-harm, typically between 0.0 and 1.0."""


class TextSafetyResult(SafetyResult):
    """A model representing the result of a text safety check."""


class ImageSafetyResult(SafetyResult):
    """A model representing the result of an image safety check."""

    is_csam: bool
    """Indicates if the content is CSAM."""


class SafetyRules:
    """A class representing the rules for content safety checks."""

    should_censor_nsfw: bool = True
    """Indicates whether NSFW content should be censored."""

    should_censor_hate_speech: bool = True
    """Indicates whether hate speech content should be censored."""

    should_censor_violent: bool = True
    """Indicates whether violent content should be censored."""

    should_censor_self_harm: bool = True
    """Indicates whether self-harm content should be censored."""

    def should_censor(self, safety_result: SafetyResult) -> bool:
        """Determine if the content should be censored based on the safety result.

        Args:
            safety_result (SafetyResult): The result of the safety check.

        Returns:
            bool: True if the content should be censored, False otherwise.
        """
        if safety_result.is_csam:
            return True

        if safety_result.is_nsfw and self.should_censor_nsfw:
            return True

        if safety_result.is_hate_speech and self.should_censor_hate_speech:
            return True

        if safety_result.is_violent and self.should_censor_violent:
            return True

        return bool(safety_result.is_self_harm and self.should_censor_self_harm)

    def __init__(
        self,
        should_censor_nsfw: bool = True,
        should_censor_hate_speech: bool = True,
        should_censor_violent: bool = True,
        should_censor_self_harm: bool = True,
    ) -> None:
        """Initialize the SafetyRules with optional parameters to set censorship preferences.

        Args:
        should_censor_nsfw (bool): Whether to censor NSFW content. Defaults to True.
        should_censor_hate_speech (bool): Whether to censor hate speech content. Defaults to True.
        should_censor_violent (bool): Whether to censor violent content. Defaults to True.
        should_censor_self_harm (bool): Whether to censor self-harm content. Defaults to True.
        """
        self.should_censor_nsfw = should_censor_nsfw
        self.should_censor_hate_speech = should_censor_hate_speech
        self.should_censor_violent = should_censor_violent
        self.should_censor_self_harm = should_censor_self_harm


default_safety_rules = SafetyRules(
    should_censor_nsfw=True,
    should_censor_hate_speech=True,
    should_censor_violent=True,
    should_censor_self_harm=True,
)

default_image_safety_rules = SafetyRules(
    should_censor_nsfw=True,
    should_censor_hate_speech=True,
    should_censor_violent=True,
    should_censor_self_harm=True,
)

default_text_safety_rules = SafetyRules(
    should_censor_nsfw=True,
    should_censor_hate_speech=True,
    should_censor_violent=True,
    should_censor_self_harm=True,
)
