"""The @action decorator - transforms classes into Qt actions."""

from collections.abc import Callable
from typing import Any, overload

from qtpy.QtGui import QAction, QIcon, QKeySequence
from qtpy.QtWidgets import QStyle

# Icon can be a path string, QIcon, or standard pixmap enum
IconType = str | QIcon | QStyle.StandardPixmap


@overload
def action[T: QAction](cls_or_text: type[T]) -> type[T]: ...


@overload
def action[T: QAction](
    cls_or_text: None = None,
    *,
    text: str | None = None,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = None,
    tooltip: str | None = None,
    icon: IconType | None = None,
    checkable: bool = False,
) -> Callable[[type[T]], type[T]]: ...


@overload
def action[T: QAction](
    cls_or_text: str,
    *,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = None,
    tooltip: str | None = None,
    icon: IconType | None = None,
    checkable: bool = False,
) -> Callable[[type[T]], type[T]]: ...


def action[T: QAction](
    cls_or_text: type[T] | str | None = None,
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
              If not provided, derived from class name (strips "Action" suffix).
        shortcut: Keyboard shortcut (e.g., "Ctrl+N" or QKeySequence.StandardKey.New).
        tooltip: Tooltip and status bar text.
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

        # Or without text (uses class name)
        @action
        class SaveAction(QAction):
            def on_triggered(self) -> None:
                print("Saving...")
    """
    # Handle @action("&New") - text as first positional arg
    if isinstance(cls_or_text, str):
        text = cls_or_text
        cls_or_text = None

    def decorator(cls: type[T]) -> type[T]:
        def new_init(self: QAction, *args: Any, **kwargs: Any) -> None:
            # Initialize QAction base class
            QAction.__init__(self)

            # Set action text
            action_text = text
            if action_text is None:
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

            # Set tooltip (both tooltip and status bar)
            if tooltip is not None:
                self.setToolTip(tooltip)
                self.setStatusTip(tooltip)

            # Set icon
            if icon is not None:
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

            # Call __setup__ hook if defined
            setup = getattr(self, "__setup__", None)
            if setup is not None and callable(setup):
                setup()

        cls.__init__ = new_init  # type: ignore[method-assign]
        return cls

    if cls_or_text is not None and not isinstance(cls_or_text, str):
        return decorator(cls_or_text)
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
