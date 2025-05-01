from pydantic import BaseModel, Field


class GenerationFeatureFlags(BaseModel):

    model_config = ConfigDict(
        use_attribute_docstrings=True,
    )

    extra_texts: bool = Field(default=False)
    """Whether there is support for extra texts."""

    extra_source_images: bool = Field(default=False)
    """Whether there is  support for extra source images."""

