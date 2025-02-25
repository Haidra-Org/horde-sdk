from pydantic import BaseModel


class BasicGenerationParameters(BaseModel):
    """Represents the common bare minimum parameters for any model-based generative inference or similar."""

    model: str
    """The model to use for the generation."""

    model_baseline: str | None
    """The baseline of the model."""
    model_filename: str | None
    """The filename of the model to use for the generation"""
    model_hash: str | None
    """The hash of the model to use for the generation"""
