from enum import auto

from pydantic import Field
from strenum import StrEnum

from horde_sdk.generic_api.apimodels import HordeAPIData


class StyleType(StrEnum):
    """An enum representing the different types of styles."""

    image = auto()
    text = auto()


class ResponseModelStylesUser(HordeAPIData):
    name: str
    """The name of the style."""
    id_: str = Field(alias="id")
    """The ID of the style."""
    type_: StyleType = Field(alias="type")
    """The type of the style."""
