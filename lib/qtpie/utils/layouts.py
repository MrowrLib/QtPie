"""Layout utility functions shared across QtPie modules."""

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
    elif layout_type == "grid":
        grid_layout = cast(QGridLayout, layout)
        if grid is not None:
            row, col = grid[0], grid[1]
            rowspan = grid[2] if len(grid) > 2 else 1
            colspan = grid[3] if len(grid) > 3 else 1
            grid_layout.addWidget(widget_instance, row, col, rowspan, colspan)
        else:
            grid_layout.addWidget(widget_instance)
