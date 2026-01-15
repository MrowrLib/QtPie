"""Layout utility functions shared across QtPie modules."""

from collections.abc import Callable
from typing import Any

from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import (
    QApplication,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from qtpie.layout import LayoutType

# Type alias for icon parameter
IconType = str | QIcon | QPixmap | QStyle.StandardPixmap | None


def resolve_icon(value: IconType) -> QIcon | None:
    """Convert str/QIcon/QPixmap/StandardPixmap to QIcon, or return None.

    Accepts:
        - str: File path or Qt resource path (e.g., ":/icons/app.png")
        - QIcon: Passed through unchanged
        - QPixmap: Converted to QIcon
        - QStyle.StandardPixmap: Resolved via application style
        - None: Returns None
    """
    if value is None:
        return None
    if isinstance(value, QIcon):
        return value
    if isinstance(value, QPixmap):
        return QIcon(value)
    if isinstance(value, QStyle.StandardPixmap):
        # Need QApplication instance to get style
        qapp = QApplication.instance()
        if qapp is not None and isinstance(qapp, QApplication):
            return qapp.style().standardIcon(value)
        return None
    # str path (file path or Qt resource path like ":/icons/app.png")
    return QIcon(value)


def create_layout(layout_type: LayoutType) -> QLayout | None:
    """Create a Qt layout based on type."""
    if layout_type == "vertical":
        return QVBoxLayout()
    elif layout_type == "horizontal":
        return QHBoxLayout()
    elif layout_type == "form":
        return QFormLayout()
    elif layout_type == "grid":
        return QGridLayout()
    return None


def add_to_layout(
    layout: QLayout,
    widget_instance: QWidget,
    layout_type: LayoutType,
    label: str | None = None,
    grid: tuple[int, ...] | None = None,
    label_translatable: Any | None = None,
) -> None:
    """Add a widget to the layout.

    Args:
        layout: The Qt layout to add to.
        widget_instance: The widget to add.
        layout_type: The type of layout.
        label: For form layouts, the label text for this row.
        grid: For grid layouts, position as (row, col) or (row, col, rowspan, colspan).
        label_translatable: Original Translatable for registering retranslation binding.
    """
    from typing import cast

    if layout_type in ("vertical", "horizontal"):
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "form":
        form_layout = cast(QFormLayout, layout)
        if label is not None:
            form_layout.addRow(label, widget_instance)
            # Register form label for retranslation if it was a Translatable
            if label_translatable is not None:
                from qtpie.translations.store import register_binding
                from qtpie.translations.translatable import Translatable

                if isinstance(label_translatable, Translatable):
                    # Get the QLabel that Qt created for this row
                    label_widget = form_layout.labelForField(widget_instance)
                    register_binding(
                        label_widget,
                        "text",
                        label_translatable.text,
                        label_translatable.context,
                    )
        else:
            form_layout.addRow(widget_instance)
        # Sync row visibility with widget visibility (for visible= bindings applied before layout)
        # Use isHidden() - isVisible() is False for widgets not yet in a shown window
        if widget_instance.isHidden():
            form_layout.setRowVisible(widget_instance, False)
    elif layout_type == "grid":
        grid_layout = cast(QGridLayout, layout)
        if grid is not None:
            row, col = grid[0], grid[1]
            rowspan = grid[2] if len(grid) > 2 else 1
            colspan = grid[3] if len(grid) > 3 else 1
            grid_layout.addWidget(widget_instance, row, col, rowspan, colspan)
        else:
            grid_layout.addWidget(widget_instance)


def apply_widget_props(
    target: Any,
    widget_props: dict[str, Any],
    skip_filter: Callable[[str, Any], bool] | None = None,
    strict: bool = False,
) -> None:
    """Apply widget properties via setter methods.

    For each prop like windowTitle="X", calls target.setWindowTitle("X").

    Args:
        target: The widget/object to apply properties to.
        widget_props: Dictionary of property names and values.
        skip_filter: Optional callable(prop_name, value) -> bool to skip certain props.
        strict: If True, raise AttributeError for missing setters.
    """
    for prop_name, value in widget_props.items():
        # Skip if filter says to
        if skip_filter is not None and skip_filter(prop_name, value):
            continue

        # Convert propName to setPropName (capitalize first letter)
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(target, setter_name, None)
        if setter is not None and callable(setter):
            setter(value)
        elif strict:
            raise AttributeError(f"{type(target).__name__} has no setter '{setter_name}' for property '{prop_name}'")


def apply_layout_margins(
    layout: QLayout,
    margins: int | tuple[int, int, int, int] | None,
) -> None:
    """Apply margins to a layout.

    Args:
        layout: The layout to configure.
        margins: Either a single int (applied to all sides) or a tuple of (left, top, right, bottom).
    """
    if margins is None:
        return
    if isinstance(margins, int):
        layout.setContentsMargins(margins, margins, margins, margins)
    else:
        layout.setContentsMargins(*margins)


def apply_object_name_and_classes(
    target: QWidget,
    object_name: str | None,
    css_classes: list[str],
    default_name: str | None = None,
) -> None:
    """Apply objectName and CSS classes to a widget.

    Args:
        target: The widget to configure.
        object_name: Explicit objectName (if set).
        css_classes: List of CSS classes to apply.
        default_name: Default objectName if not explicitly set.
    """
    # Apply objectName: use explicit name if set, otherwise use default
    if object_name is not None:
        target.setObjectName(object_name)
    elif default_name is not None:
        target.setObjectName(default_name)

    # Apply CSS classes if specified
    if css_classes:
        from qtpie.styles import set_classes

        set_classes(target, css_classes)
