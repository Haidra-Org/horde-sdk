from enum import auto

from strenum import StrEnum


class KNOWN_AUX_MODEL_SOURCE(StrEnum):
    """The known sources of an auxiliary model (aux models are LoRas, TIs, etc)."""

    LOCAL = auto()
    """The aux model is worker-provided on their local machine."""

    CIVITAI = auto()
    """The aux model is provided by CivitAI."""

    HORDELING = auto()
    """The aux model is provided by the AI-Horde hordeling service."""
