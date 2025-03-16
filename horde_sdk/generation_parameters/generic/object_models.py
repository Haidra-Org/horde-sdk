from pydantic import BaseModel, Field


class GenerationFeatureFlags(BaseModel):
    extra_texts: bool = Field(default=False)
    """Whether the worker supports extra texts."""

    extra_source_images: bool = Field(default=False)
    """Whether the worker supports extra source images."""
