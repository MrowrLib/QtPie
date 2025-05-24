from dataclasses import dataclass, is_dataclass
from typing import Callable, TypeVar, cast, dataclass_transform, overload

from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from qtpie.styles.classes import add_classes
from qtpie.types.widget_layout_type import WidgetLayoutType

T = TypeVar("T", bound=type)


def _widget_impl(
    cls: T,
    name: str | None = None,
    layout: WidgetLayoutType | None = None,
    classes: list[str] | None = None,
) -> T:
    """Core widget setup logic shared by both decorators."""
    if not issubclass(cls, QWidget):
        raise TypeError(f"Widget decorator can only be applied to QWidget subclasses, got {cls.__name__}")

    def _finalize_widget(self: QWidget) -> None:
        self.setObjectName(name or type(self).__name__)

        # Set layout if specified
        if layout == "horizontal":
            self.setLayout(QHBoxLayout())
        elif layout == "vertical":
            self.setLayout(QVBoxLayout())
        elif layout == "grid":
            self.setLayout(QGridLayout())
        elif layout == "form":
            self.setLayout(QFormLayout())

        # Add classes if provided
        if classes is not None:
            add_classes(self, classes)

        # Future: call setup() if present
        if hasattr(self, "setup"):
            self.setup()

    if is_dataclass(cls):
        orig_init = cls.__init__

        def __init__(self: QWidget, *args: object, **kwargs: object) -> None:
            QWidget.__init__(self)
            orig_init(self, *args, **kwargs)
            _finalize_widget(self)

        cls.__init__ = __init__
        return cls
    else:
        orig_init = cls.__init__

        def defines_custom_init(c: type) -> bool:
            # True if c or any base except QWidget/object defines __init__ directly
            for base in c.__mro__:
                if base is QWidget or base is object:
                    continue
                if "__init__" in base.__dict__:
                    return True
            return False

        if defines_custom_init(cls):

            def __init__(self: QWidget, *args: object, **kwargs: object) -> None:
                orig_init(self, *args, **kwargs)
                _finalize_widget(self)

            cls.__init__ = __init__
            return cls
        else:
            # Use a metaclass to inject _finalize_widget after construction
            class WidgetMeta(type(cls)):
                def __call__(meta_cls, *args, **kwargs):
                    instance = super().__call__(*args, **kwargs)
                    if isinstance(instance, QWidget):
                        _finalize_widget(instance)
                    return instance

            # Dynamically create a subclass with the new metaclass
            new_cls = WidgetMeta(cls.__name__, (cls,), dict(cls.__dict__))
            return new_cls


@overload
def widget_class(
    cls: T,
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> T: ...
@overload
def widget_class(
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> Callable[[T], T]: ...
@overload
def widget_class() -> Callable[[T], T]: ...


def widget_class(
    cls: T | None = None,
    *,
    name: str | None = None,
    layout: WidgetLayoutType | None = "vertical",
    classes: list[str] | None = None,
) -> T | Callable[[T], T]:
    """
    Decorator for manual-init QWidget subclasses.

    IMPORTANT:
    Do NOT call super().__init__() in your __init__ method.
    The decorator will call QWidget.__init__() for you before your __init__ runs.
    Calling super().__init__() yourself will result in double-initialization and a RuntimeError.
    """

    def decorator(cls: T) -> T:
        return _widget_impl(cls, name=name, layout=layout, classes=classes)

    return decorator if cls is None else decorator(cls)


@overload
def widget(
    cls: T,
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> T: ...
@overload
def widget(
    *,
    name: str | None = ...,
    layout: WidgetLayoutType | None = ...,
    classes: list[str] | None = ...,
) -> Callable[[T], T]: ...
@overload
def widget() -> Callable[[T], T]: ...


@dataclass_transform()
def widget(
    cls: T | None = None,
    *,
    name: str | None = None,
    layout: WidgetLayoutType | None = "vertical",
    classes: list[str] | None = None,
) -> T | Callable[[T], T]:
    """Decorator that makes a class a dataclass with Qt widget capabilities."""

    def decorator(cls: T) -> T:
        if not issubclass(cls, QWidget):
            raise TypeError(f"@widget can only be applied to QWidget subclasses, got {cls.__name__}")

        dataclass_cls = cast(T, dataclass(cls))
        return _widget_impl(dataclass_cls, name=name, layout=layout, classes=classes)

    return decorator if cls is None else decorator(cls)
