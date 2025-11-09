from enum import auto

from strenum import StrEnum

from horde_sdk.consts import KNOWN_SERVICE


class UNDERLYING_GENERATION_SCHEME(StrEnum):
    """The underlying method the generation uses to produce results.

    In the case that an outside service is used to produce results, this should be set to `MODEL_FROM_SERVICE`.
    This is to prevent potential confusion by identifying a service name as the "model".

    Most generative AI is model-based, but certain alchemy or other operations may not have a traditional model
    and instead use alternative methods and in this case you can use `NON_MODEL_ALGORITHM` to indicate that.
    """

    MODEL = auto()

    MODEL_FROM_SERVICE = auto()

    NON_MODEL_ALGORITHM = auto()


class KNOWN_AUX_MODEL_SOURCE(StrEnum):
    """The known sources of an auxiliary model (aux models are LoRas, TIs, etc)."""

    LOCAL = auto()
    """The aux model is worker-provided on their local machine."""

    CIVITAI = auto()
    """The aux model is provided by CivitAI."""

    HORDELING = auto()
    """The aux model is provided by the AI-Horde hordeling service."""

    def map_to_known_service(self) -> KNOWN_SERVICE:
        """Map the aux model source to a known service."""
        if self == KNOWN_AUX_MODEL_SOURCE.CIVITAI:
            return KNOWN_SERVICE.CIVITAI
        if self == KNOWN_AUX_MODEL_SOURCE.HORDELING:
            return KNOWN_SERVICE.AI_HORDE
        return KNOWN_SERVICE.UNKNOWN
