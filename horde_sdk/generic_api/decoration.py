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

    def __hash__(self) -> int:  # type: ignore # noqa: ANN001
        raise NotImplementedError(f"Hashing is not implemented for {cls.__name__}")

    cls.__hash__ = __hash__  # type: ignore

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


def Unequatable(cls: type[T]) -> type[T]:
    """A decorator that makes a class unequatable

    Args:
        cls (type[T]): The class to make unequatable

    Returns:
        type[T]: The unequatable class
    """

    cls._unequatable = True  # type: ignore

    def __eq__(self, other: Any) -> bool:  # type: ignore # noqa: ANN001, ANN401
        raise NotImplementedError(f"Equality is not implemented for {cls.__name__}")

    cls.__eq__ = __eq__  # type: ignore

    return cls


def is_unequatable(obj: type | Any) -> bool:  # noqa: ANN401
    """Check if an object is unequatable.

    Args:
        obj (Any): The object to check.

    Returns:
        bool: True if the object is unequatable, False otherwise.
    """
    cls = obj.__class__ if not isinstance(obj, type) else obj

    return getattr(cls, "_unequatable", False)
