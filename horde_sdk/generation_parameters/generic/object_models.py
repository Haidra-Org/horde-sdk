from abc import ABC, abstractmethod
from typing import Any

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


class ModelRecordResolver(ABC):
    """Abstract base class for classes responsible for resolving model records from a service or data source."""

    @abstractmethod
    def resolve_model_by_name(
        self,
        model_name: str,
    ) -> BaseModel | dict[Any, Any] | None:
        """Resolve a model by its name.

        Args:
            model_name: The name of the model to resolve.

        Returns:
            The resolved model record, or None if not found.
        """
