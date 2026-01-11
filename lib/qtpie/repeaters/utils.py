"""Shared utilities for repeater classes."""

from collections.abc import Callable
from typing import Any

from observant import Observable, ObservableProxy
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qtpie.utils.common import is_primitive_type


def resolve_sort[T](
    sort: bool | str | Callable[[T], Any] | None,
    parent_widget: Any | None,
) -> bool | Callable[[T], Any] | None:
    """Resolve sort= parameter, converting string method names to callables.

    Args:
        sort: The sort parameter value.
        parent_widget: The parent widget for resolving method names.

    Returns:
        Resolved sort value (bool, callable, or None).

    Raises:
        AttributeError: If a string method name cannot be resolved.
    """
    if sort is None or isinstance(sort, bool) or callable(sort):
        return sort
    # String method name - resolve from parent widget
    if parent_widget is not None:
        method = getattr(parent_widget, sort, None)
        if method is not None and callable(method):
            return method
        raise AttributeError(f"sort='{sort}' - method not found on {type(parent_widget).__name__}")
    raise AttributeError(f"sort='{sort}' - cannot resolve method name without parent widget")


def create_item_wrapper(
    item: Any,
    item_type: type | None,
) -> Observable[Any] | ObservableProxy[Any]:
    """Create the appropriate wrapper for an item.

    Args:
        item: The item to wrap.
        item_type: The type of the item.

    Returns:
        Observable for primitives, ObservableProxy for objects.
    """
    if is_primitive_type(item_type):
        return Observable(item)
    else:
        return ObservableProxy(item)


def create_styled_widget(
    widget_type: type,
    widget_args: tuple[Any, ...],
    widget_kwargs: dict[str, Any],
    object_name: str | None,
    css_classes: list[str],
    widget_props: dict[str, Any],
) -> QWidget:
    """Create a widget with styling applied.

    This is the shared widget creation logic for repeaters.

    Args:
        widget_type: The widget class to instantiate.
        widget_args: Positional arguments for constructor.
        widget_kwargs: Keyword arguments for constructor.
        object_name: objectName to set (if any).
        css_classes: CSS classes to apply.
        widget_props: Widget properties to apply via setXxx().

    Returns:
        The created and styled widget.
    """
    widget = widget_type(*widget_args, **widget_kwargs)

    # Apply objectName if specified
    if object_name is not None:
        widget.setObjectName(object_name)

    # Apply CSS classes if specified
    if css_classes:
        from qtpie.styles import set_classes

        set_classes(widget, list(css_classes))

    # Apply widget props (styleSheet="X" → setStyleSheet("X"))
    for prop_name, value in widget_props.items():
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(widget, setter_name, None)
        if setter is not None and callable(setter):
            setter(value)

    return widget


def setup_repeater_layout(
    parent: QWidget,
    layout_type: str,
) -> QVBoxLayout | QHBoxLayout:
    """Set up a repeater's layout.

    Args:
        parent: The parent widget to set layout on.
        layout_type: "vertical" or "horizontal".

    Returns:
        The created layout.
    """
    if layout_type == "horizontal":
        layout = QHBoxLayout(parent)
    else:
        layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout
