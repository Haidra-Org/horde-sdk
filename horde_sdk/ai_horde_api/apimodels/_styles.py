from enum import auto

from pydantic import Field
from strenum import StrEnum

from horde_sdk.generic_api.apimodels import HordeAPIDataObject


class StyleType(StrEnum):
    """An enum representing the different types of styles."""

    image = auto()
    text = auto()


class ResponseModelStylesUser(HordeAPIDataObject):
    name: str
    id_: str = Field(alias="id")
    type_: StyleType = Field(alias="type")
