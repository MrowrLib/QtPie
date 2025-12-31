"""The @window decorator - transforms classes into Qt main windows."""

from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields
from typing import (
    Any,
    dataclass_transform,
    get_type_hints,
    overload,
)

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QMainWindow, QMenu, QWidget

from qtpie.decorators._async_wrap import wrap_async_methods
from qtpie.factories.make import SIGNALS_METADATA_KEY
from qtpie.screen import center_on_screen


@overload
@dataclass_transform()
def window[T: QMainWindow](
    _cls: type[T],
    *,
    name: str | None = ...,
    classes: list[str] | None = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    icon: str | None = ...,
    center: bool = ...,
) -> type[T]: ...


@overload
@dataclass_transform()
def window[T: QMainWindow](
    _cls: None = None,
    *,
    name: str | None = ...,
    classes: list[str] | None = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    icon: str | None = ...,
    center: bool = ...,
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform()
def window[T: QMainWindow](
    _cls: type[T] | None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    size: tuple[int, int] | None = None,
    icon: str | None = None,
    center: bool = False,
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Decorator that transforms a class into a Qt main window.

    Args:
        name: Object name for QSS styling (defaults to class name).
        classes: CSS-like classes for styling.
        title: Window title.
        size: Window size as (width, height).
        icon: Path to window icon file.
        center: Whether to center the window on screen.

    Example:
        @window(title="My App", size=(1024, 768), center=True)
        class MainWindow(QMainWindow):
            editor: QTextEdit = make(QTextEdit)

            def setup(self) -> None:
                self.statusBar().showMessage("Ready")
    """

    def decorator(cls: type[T]) -> type[T]:
        # Auto-wrap async methods (e.g., async def closeEvent)
        wrap_async_methods(cls)

        # Apply @dataclass to register fields
        cls = dataclass(cls)  # type: ignore[assignment]

        def new_init(self: QMainWindow, *args: object, **kwargs: object) -> None:
            # Initialize QMainWindow base class first
            QMainWindow.__init__(self)

            # Manually set dataclass fields (with default_factory support)
            for f in fields(cls):  # type: ignore[arg-type]
                if f.name in kwargs:
                    setattr(self, f.name, kwargs[f.name])
                elif f.default is not MISSING:
                    setattr(self, f.name, f.default)
                elif f.default_factory is not MISSING:  # type: ignore[arg-type]
                    setattr(self, f.name, f.default_factory())  # type: ignore[misc]

            # Connect signals from make() metadata
            for f in fields(cls):  # type: ignore[arg-type]
                potential_signals = f.metadata.get(SIGNALS_METADATA_KEY)
                if potential_signals:
                    widget_instance = getattr(self, f.name, None)
                    if widget_instance is not None:
                        _connect_signals(self, widget_instance, potential_signals)

            # Set object name
            if name:
                self.setObjectName(name)
            elif not self.objectName():
                object_name = cls.__name__
                if object_name.endswith("Window"):
                    object_name = object_name[:-6]
                self.setObjectName(object_name)

            # Set CSS-like classes
            if classes:
                _set_classes(self, classes)

            # Set window title
            if title:
                self.setWindowTitle(title)

            # Set window icon
            if icon:
                self.setWindowIcon(QIcon(icon))

            # Set window size
            if size:
                self.resize(size[0], size[1])

            # Auto-set central widget if field exists
            type_hints = get_type_hints(cls)
            for f in fields(cls):  # type: ignore[arg-type]
                if f.name.startswith("_"):
                    continue

                field_type = type_hints.get(f.name)

                # Check for central_widget field
                if f.name == "central_widget":
                    widget_instance = getattr(self, f.name, None)
                    if isinstance(widget_instance, QWidget):
                        self.setCentralWidget(widget_instance)
                    continue

                # Auto-add QMenu fields to menu bar
                if isinstance(field_type, type) and issubclass(field_type, QMenu):
                    menu_instance = getattr(self, f.name, None)
                    if isinstance(menu_instance, QMenu):
                        self.menuBar().addMenu(menu_instance)

            # Lifecycle hooks
            _call_if_exists(self, "configure")
            _call_if_exists(self, "setup")

            # Center on screen (must be done after size is set)
            if center:
                center_on_screen(self)

        cls.__init__ = new_init  # type: ignore[method-assign]
        return cls

    if _cls is not None:
        return decorator(_cls)
    return decorator


def _connect_signals(
    parent: object,
    widget_instance: object,
    potential_signals: dict[str, str | Callable[..., Any]],
) -> None:
    """Connect signals from make() metadata to methods or callables."""
    for attr_name, handler in potential_signals.items():
        attr = getattr(widget_instance, attr_name, None)
        if attr is not None and hasattr(attr, "connect"):
            if isinstance(handler, str):
                method = getattr(parent, handler, None)
                if method is not None:
                    attr.connect(method)
            elif callable(handler):
                attr.connect(handler)
        else:
            setter_name = f"set{attr_name[0].upper()}{attr_name[1:]}"
            setter = getattr(widget_instance, setter_name, None)
            if setter is not None and callable(setter):
                setter(handler)


def _set_classes(widget: QWidget, class_list: list[str]) -> None:
    """Set CSS-like classes on a widget as a Qt property."""
    widget.setProperty("class", class_list)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _call_if_exists(obj: object, method_name: str, *args: object) -> None:
    """Call a method on obj if it exists and is callable."""
    method = getattr(obj, method_name, None)
    if method is not None and callable(method):
        method(*args)
