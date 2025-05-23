from dataclasses import dataclass
from typing import Callable, TypeVar, cast, dataclass_transform, overload

from qtpy.QtWidgets import QWidget

T = TypeVar("T", bound=type)


@overload
def widget(cls: T) -> T: ...


@overload
def widget() -> Callable[[T], T]: ...


@dataclass_transform()
def widget(cls: T | None = None) -> T | Callable[[T], T]:
    """Decorator that makes a class a dataclass with Qt widget capabilities."""

    def decorator(cls: T) -> T:
        if not issubclass(cls, QWidget):
            raise TypeError(f"@widget can only be applied to QWidget subclasses, got {cls.__name__}")
        return cast(T, dataclass(cls))

    if cls is None:
        return decorator
    else:
        return decorator(cls)
