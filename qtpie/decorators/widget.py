from dataclasses import dataclass
from typing import Callable, TypeVar, cast, dataclass_transform, overload

from qtpy.QtWidgets import QWidget

T = TypeVar("T", bound=type)


def _widget_impl(cls: T) -> T:
    """Core widget setup logic shared by both decorators."""
    if not issubclass(cls, QWidget):
        raise TypeError(f"Widget decorator can only be applied to QWidget subclasses, got {cls.__name__}")

    orig_init = cls.__init__

    def __init__(self, *args: object, **kwargs: object) -> None:
        orig_init(self, *args, **kwargs)
        super(type(self), self).__init__()
        self.setObjectName(type(self).__name__)

    cls.__init__ = __init__
    return cls


@overload
def widget_class(cls: T) -> T: ...
@overload
def widget_class() -> Callable[[T], T]: ...
def widget_class(cls: T | None = None) -> T | Callable[[T], T]:
    def decorator(cls: T) -> T:
        return _widget_impl(cls)

    return decorator if cls is None else decorator(cls)


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

        def __init__(self, *args: object, **kwargs: object) -> None:
            orig_init(self, *args, **kwargs)
            super(type(self), self).__init__()  # ✅ important: init QWidget manually
            self.setObjectName(type(self).__name__)  # safer than using captured `cls`

        dataclass_cls.__init__ = __init__
        return dataclass_cls

    return decorator if cls is None else decorator(cls)
