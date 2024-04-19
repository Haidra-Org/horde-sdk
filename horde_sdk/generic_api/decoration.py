from typing import Any, TypeVar

T = TypeVar("T")


def Unhashable(cls: type[T]) -> type[T]:
    """A decorator that makes a class unhashable.

    Args:
        cls (Any): The class to make unhashable.

    Returns:
        Any: The unhashable class.
    """
    cls._unhashable = True  # type: ignore
    return cls


def is_unhashable(obj: type | Any) -> bool:  # noqa: ANN401
    """Check if an object is unhashable.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if the object is unhashable, False otherwise.
    """
    cls = obj.__class__ if not isinstance(obj, type) else obj

    return getattr(cls, "_unhashable", False)
