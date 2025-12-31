"""The @action decorator - transforms classes into Qt actions."""

from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields
from typing import (
    Any,
    dataclass_transform,
    overload,
)

from qtpy.QtGui import QAction, QIcon, QKeySequence
from qtpy.QtWidgets import QStyle

from qtpie.factories.make import SIGNALS_METADATA_KEY

# Icon can be a path string, QIcon, or standard pixmap enum
IconType = str | QIcon | QStyle.StandardPixmap


@overload
@dataclass_transform()
def action[T: QAction](
    _cls_or_text: type[T],
    *,
    text: str | None = ...,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = ...,
    tooltip: str | None = ...,
    icon: IconType | None = ...,
    checkable: bool = ...,
) -> type[T]: ...


@overload
@dataclass_transform()
def action[T: QAction](
    _cls_or_text: None = None,
    *,
    text: str | None = ...,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = ...,
    tooltip: str | None = ...,
    icon: IconType | None = ...,
    checkable: bool = ...,
) -> Callable[[type[T]], type[T]]: ...


@overload
@dataclass_transform()
def action[T: QAction](
    _cls_or_text: str,
    *,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = ...,
    tooltip: str | None = ...,
    icon: IconType | None = ...,
    checkable: bool = ...,
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform()
def action[T: QAction](
    _cls_or_text: type[T] | str | None = None,
    *,
    text: str | None = None,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = None,
    tooltip: str | None = None,
    icon: IconType | None = None,
    checkable: bool = False,
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Decorator that transforms a class into a Qt action.

    Args:
        text: Action text (shown in menu). Can be passed as first positional arg.
        shortcut: Keyboard shortcut (e.g., "Ctrl+N" or QKeySequence.New).
        tooltip: Tooltip/status bar text.
        icon: Icon as path string, QIcon, or QStyle.StandardPixmap.
        checkable: Whether action is checkable (toggle).

    Features:
        - Auto-connect `triggered` signal to `on_triggered()` method if it exists
        - Auto-connect `toggled` signal to `on_toggled()` method if it exists

    Example:
        @action("&New", shortcut="Ctrl+N", tooltip="Create a new file")
        class NewAction(QAction):
            def on_triggered(self) -> None:
                print("Creating new file...")

        @action("&Bold", shortcut="Ctrl+B", checkable=True)
        class BoldAction(QAction):
            def on_toggled(self, checked: bool) -> None:
                print(f"Bold: {checked}")
    """
    # Handle @action("&New") - text as first positional arg
    if isinstance(_cls_or_text, str):
        text = _cls_or_text
        _cls_or_text = None

    def decorator(cls: type[T]) -> type[T]:
        # Apply @dataclass to register fields
        cls = dataclass(cls)  # type: ignore[assignment]

        def new_init(self: QAction, *args: object, **kwargs: object) -> None:
            # Initialize QAction base class first
            QAction.__init__(self)

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
                    instance = getattr(self, f.name, None)
                    if instance is not None:
                        _connect_signals(self, instance, potential_signals)

            # Set action text
            if text:
                self.setText(text)
            else:
                # Auto-generate from class name
                action_text = cls.__name__
                if action_text.endswith("Action"):
                    action_text = action_text[:-6]
                self.setText(action_text)

            # Set shortcut
            if shortcut is not None:
                if isinstance(shortcut, str):
                    self.setShortcut(QKeySequence(shortcut))
                elif isinstance(shortcut, QKeySequence):
                    self.setShortcut(shortcut)
                else:
                    # QKeySequence.StandardKey
                    self.setShortcut(QKeySequence(shortcut))

            # Set tooltip (shown in status bar)
            if tooltip:
                self.setStatusTip(tooltip)
                self.setToolTip(tooltip)

            # Set icon
            if icon:
                _set_icon(self, icon)

            # Set checkable
            if checkable:
                self.setCheckable(True)

            # Auto-connect triggered signal to on_triggered method
            on_triggered = getattr(self, "on_triggered", None)
            if on_triggered is not None and callable(on_triggered):
                self.triggered.connect(on_triggered)

            # Auto-connect toggled signal to on_toggled method
            on_toggled = getattr(self, "on_toggled", None)
            if on_toggled is not None and callable(on_toggled):
                self.toggled.connect(on_toggled)

            # Call lifecycle hooks if they exist
            _call_if_exists(self, "setup")

        cls.__init__ = new_init  # type: ignore[method-assign]
        return cls

    if _cls_or_text is not None and not isinstance(_cls_or_text, str):
        return decorator(_cls_or_text)
    return decorator


def _set_icon(qaction: QAction, icon: IconType) -> None:
    """Set icon on action from various sources."""
    if isinstance(icon, str):
        qaction.setIcon(QIcon(icon))
    elif isinstance(icon, QIcon):
        qaction.setIcon(icon)
    else:
        # QStyle.StandardPixmap - get standard icon from application style
        from qtpy.QtWidgets import QApplication

        app = QApplication.instance()
        if isinstance(app, QApplication):
            qaction.setIcon(app.style().standardIcon(icon))


def _connect_signals(
    parent: object,
    instance: object,
    potential_signals: dict[str, str | Callable[..., Any]],
) -> None:
    """Connect signals from make() metadata to methods or callables."""
    for attr_name, handler in potential_signals.items():
        attr = getattr(instance, attr_name, None)
        if attr is not None and hasattr(attr, "connect"):
            if isinstance(handler, str):
                method = getattr(parent, handler, None)
                if method is not None:
                    attr.connect(method)
            elif callable(handler):
                attr.connect(handler)


def _call_if_exists(obj: object, method_name: str, *args: object) -> None:
    """Call a method on obj if it exists and is callable."""
    method = getattr(obj, method_name, None)
    if method is not None and callable(method):
        method(*args)
