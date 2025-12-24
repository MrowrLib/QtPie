from dataclasses import field
from typing import Any, ParamSpec, TypeVar

T = TypeVar("T", covariant=True)
P = ParamSpec("P")


def make_later[T](class_type: type[T], *args: Any, **kwargs: Any) -> T:
    """
    Creates a factory for any dataclass field which you must initialize later.

    This is useful for fields that require a parent or other dependencies to be set first.

    Returns an object of type T for type checking, but at runtime returns a dataclass field.

    This type lie is intentional to make the API more ergonomic while maintaining type safety.
    """

    return field(init=False)
