"""GroupBox - QGroupBox with QtPie declarative features."""

# pyright: reportPrivateUsage=false

from collections.abc import Callable
from typing import Any, overload

from qtpy.QtWidgets import QGroupBox

from .layout import LayoutType
from .widget import widget
from .widget_base import WidgetBase


class GroupBox[T = None](QGroupBox, WidgetBase[T]):
    """QGroupBox with QtPie declarative features.

    Use this as a base for titled container components.
    Supports title, checkable, flat, and other QGroupBox properties.

    Example:
        @groupbox("Settings")
        class SettingsBox(GroupBox):
            _option1: QCheckBox = new("Enable feature")
            _option2: QCheckBox = new("Show notifications")

        @groupbox("Advanced", checkable=True)
        class AdvancedSettings(GroupBox):
            _detail: QLineEdit = new()

    With record type:
        @groupbox("Person Details")
        class PersonBox(GroupBox[Person]):
            name: QLineEdit = new()  # Auto-binds to record.name
            age: QSpinBox = new()    # Auto-binds to record.age
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @groupbox decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @groupbox. Add @groupbox above your class definition.")
        # This should never run - @groupbox replaces __init__
        super().__init__(*args, **kwargs)  # pragma: no cover


# Decorator overloads for proper type hints
@overload
def groupbox[G: GroupBox[Any]](cls: type[G]) -> type[G]: ...


@overload
def groupbox[G: GroupBox[Any]](
    cls: str,
    *,
    layout: LayoutType = "vertical",
    **kwargs: Any,
) -> Callable[[type[G]], type[G]]: ...


@overload
def groupbox[G: GroupBox[Any]](
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    title: str | None = None,
    **kwargs: Any,
) -> Callable[[type[G]], type[G]]: ...


def groupbox[G: GroupBox[Any]](  # pyright: ignore[reportInconsistentOverload]
    cls: type[G] | str | None = None,
    *,
    layout: LayoutType = "vertical",
    title: str | None = None,
    **kwargs: Any,
) -> type[G] | Callable[[type[G]], type[G]]:
    """Decorator for GroupBox classes.

    Supports optional title as first positional argument:
        @groupbox("Settings")
        class SettingsBox(GroupBox): ...

        @groupbox("Options", checkable=True)
        class OptionsBox(GroupBox): ...

        @groupbox
        class PlainBox(GroupBox): ...

    Args:
        cls: The class to decorate, or a title string.
        layout: Layout type ("vertical", "horizontal", "form", "grid", None).
        title: GroupBox title (can also be passed as first positional arg).
        **kwargs: Additional QGroupBox properties (checkable, flat, etc.).
    """
    # Determine the actual title
    actual_title: str | None = None
    if isinstance(cls, str):
        actual_title = cls
        cls = None
    elif title is not None:
        actual_title = title

    # Get the widget decorator result
    # After the isinstance check above, cls is either type[G] or None
    widget_decorator = widget(cls=cls, layout=layout, **kwargs)  # type: ignore[arg-type]

    # If cls was provided (bare @groupbox), widget returns the decorated class
    if not callable(widget_decorator) or (cls is not None and isinstance(widget_decorator, type)):
        # Direct decoration - apply title if present
        if actual_title is not None and hasattr(widget_decorator, "setTitle"):
            # This shouldn't happen for groupbox since we don't pass cls when we have a title
            pass
        return widget_decorator  # type: ignore[return-value]

    # widget returned a decorator function - wrap it to apply title
    def decorator_with_title(target: type[G]) -> type[G]:
        decorated = widget_decorator(target)  # type: ignore[arg-type]
        # Store title in widget_props so it gets applied
        if actual_title is not None:
            decorated._qtpie_config.widget_props["title"] = actual_title
        return decorated  # type: ignore[return-value]

    return decorator_with_title
