from pydantic import BaseModel, ConfigDict, Field


class GenerationFeatureFlags(BaseModel):
    """Base class for all generation features flags, which represent what support is either required or available."""

    model_config = ConfigDict(
        use_attribute_docstrings=True,
    )

    extra_texts: bool = Field(default=False)
    """Whether there is support for extra texts."""

    extra_source_images: bool = Field(default=False)
    """Whether there is  support for extra source images."""
