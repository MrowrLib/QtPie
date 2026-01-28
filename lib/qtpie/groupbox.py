"""GroupBox - QGroupBox with QtPie declarative features."""

# pyright: reportPrivateUsage=false

from collections.abc import Callable
from typing import Any, overload

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QGroupBox

from .layout import FieldGrowthPolicy, LayoutType, RowWrapPolicy, SizeConstraint
from .utils.layouts import IconType
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
    margins: int | tuple[int, int, int, int] = 0,
    marginLeft: int | None = None,
    marginTop: int | None = None,
    marginRight: int | None = None,
    marginBottom: int | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    width: int | None = None,
    height: int | None = None,
    record: Any | None = None,
    attributes: dict[Qt.WidgetAttribute, bool] | tuple[Qt.WidgetAttribute, ...] | None = None,
    styledBackground: bool = False,
    # Layout configuration
    spacing: int = 0,
    size_constraint: SizeConstraint | None = None,
    horizontal_spacing: int | None = None,
    vertical_spacing: int | None = None,
    row_wrap_policy: RowWrapPolicy | None = None,
    label_alignment: Qt.AlignmentFlag | None = None,
    form_alignment: Qt.AlignmentFlag | None = None,
    field_growth_policy: FieldGrowthPolicy | None = None,
    **kwargs: Any,
) -> Callable[[type[G]], type[G]]: ...


@overload
def groupbox[G: GroupBox[Any]](
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    title: str | None = None,
    margins: int | tuple[int, int, int, int] = 0,
    marginLeft: int | None = None,
    marginTop: int | None = None,
    marginRight: int | None = None,
    marginBottom: int | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    width: int | None = None,
    height: int | None = None,
    record: Any | None = None,
    attributes: dict[Qt.WidgetAttribute, bool] | tuple[Qt.WidgetAttribute, ...] | None = None,
    styledBackground: bool = False,
    # Layout configuration
    spacing: int = 0,
    size_constraint: SizeConstraint | None = None,
    horizontal_spacing: int | None = None,
    vertical_spacing: int | None = None,
    row_wrap_policy: RowWrapPolicy | None = None,
    label_alignment: Qt.AlignmentFlag | None = None,
    form_alignment: Qt.AlignmentFlag | None = None,
    field_growth_policy: FieldGrowthPolicy | None = None,
    **kwargs: Any,
) -> Callable[[type[G]], type[G]]: ...


def groupbox[G: GroupBox[Any]](  # pyright: ignore[reportInconsistentOverload]
    cls: type[G] | str | None = None,
    *,
    layout: LayoutType = "vertical",
    title: str | None = None,
    margins: int | tuple[int, int, int, int] = 0,
    marginLeft: int | None = None,
    marginTop: int | None = None,
    marginRight: int | None = None,
    marginBottom: int | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    width: int | None = None,
    height: int | None = None,
    record: Any | None = None,
    attributes: dict[Qt.WidgetAttribute, bool] | tuple[Qt.WidgetAttribute, ...] | None = None,
    styledBackground: bool = False,
    # Layout configuration
    spacing: int = 0,
    size_constraint: SizeConstraint | None = None,
    horizontal_spacing: int | None = None,
    vertical_spacing: int | None = None,
    row_wrap_policy: RowWrapPolicy | None = None,
    label_alignment: Qt.AlignmentFlag | None = None,
    form_alignment: Qt.AlignmentFlag | None = None,
    field_growth_policy: FieldGrowthPolicy | None = None,
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
        margins: Layout margins. int applies to all sides, or tuple (left, top, right, bottom).
        auto_bind: Whether to auto-bind fields to record properties.
        name: Widget object name.
        classes: CSS classes for styling.
        icon: Window icon.
        size: Fixed size (width, height).
        width: Fixed width.
        height: Fixed height.
        record: Record instance for Widget[T] pattern.
        attributes: Qt widget attributes to set.
        styledBackground: Enable styled background.
        spacing: Layout spacing.
        size_constraint: Layout size constraint.
        horizontal_spacing: Horizontal spacing (grid/form layouts).
        vertical_spacing: Vertical spacing (grid/form layouts).
        row_wrap_policy: Form layout row wrap policy.
        label_alignment: Form layout label alignment.
        form_alignment: Form layout form alignment.
        field_growth_policy: Form layout field growth policy.
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
    widget_decorator = widget(
        cls=cls,  # type: ignore[arg-type]
        layout=layout,
        margins=margins,
        marginLeft=marginLeft,
        marginTop=marginTop,
        marginRight=marginRight,
        marginBottom=marginBottom,
        auto_bind=auto_bind,
        name=name,
        classes=classes,
        icon=icon,
        size=size,
        width=width,
        height=height,
        record=record,
        attributes=attributes,
        styledBackground=styledBackground,
        spacing=spacing,
        size_constraint=size_constraint,
        horizontal_spacing=horizontal_spacing,
        vertical_spacing=vertical_spacing,
        row_wrap_policy=row_wrap_policy,
        label_alignment=label_alignment,
        form_alignment=form_alignment,
        field_growth_policy=field_growth_policy,
        **kwargs,
    )

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
