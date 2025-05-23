from dataclasses import dataclass
from typing import Callable, TypeVar, cast, dataclass_transform, overload

from qtpy.QtWidgets import QWidget

T = TypeVar("T", bound=type)

print("widget decorator loaded")


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

        dataclass_cls = cast(T, dataclass(cls))

        orig_init = dataclass_cls.__init__

        def __init__(self, *args, **kwargs) -> None:
            orig_init(self, *args, **kwargs)
            super(type(self), self).__init__()  # ✅ important: init QWidget manually
            self.setObjectName(type(self).__name__)  # safer than using captured `cls`

        dataclass_cls.__init__ = __init__
        return dataclass_cls

    return decorator if cls is None else decorator(cls)
