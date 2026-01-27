"""Layout utility functions shared across QtPie modules."""

from collections.abc import Callable
from typing import Any, Literal

from qtpy.QtCore import Qt
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

from qtpie.layout import FieldGrowthPolicy, LayoutType, RowWrapPolicy, SizeConstraint

# Type alias for icon parameter
# - None: inherit from parent/active window (default)
# - False: explicitly no icon
# - str/QIcon/QPixmap/StandardPixmap: explicit icon
IconType = str | QIcon | QPixmap | QStyle.StandardPixmap | Literal[False] | None


def resolve_icon(value: IconType) -> QIcon | None:
    """Convert str/QIcon/QPixmap/StandardPixmap to QIcon, or return None.

    Accepts:
        - str: File path or Qt resource path (e.g., ":/icons/app.png")
        - QIcon: Passed through unchanged
        - QPixmap: Converted to QIcon
        - QStyle.StandardPixmap: Resolved via application style
        - False: Explicit opt-out, returns None
        - None: Returns None
    """
    if value is None or value is False:
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


def _get_size_constraint(value: SizeConstraint) -> QLayout.SizeConstraint:
    """Convert SizeConstraint string to Qt enum."""
    mapping: dict[SizeConstraint, QLayout.SizeConstraint] = {
        "default": QLayout.SizeConstraint.SetDefaultConstraint,
        "fixed": QLayout.SizeConstraint.SetFixedSize,
        "minimum": QLayout.SizeConstraint.SetMinimumSize,
        "maximum": QLayout.SizeConstraint.SetMaximumSize,
        "min_max": QLayout.SizeConstraint.SetMinAndMaxSize,
        "no_constraint": QLayout.SizeConstraint.SetNoConstraint,
    }
    return mapping.get(value, QLayout.SizeConstraint.SetDefaultConstraint)


def _get_row_wrap_policy(value: RowWrapPolicy) -> QFormLayout.RowWrapPolicy:
    """Convert RowWrapPolicy string to Qt enum."""
    mapping: dict[RowWrapPolicy, QFormLayout.RowWrapPolicy] = {
        "dont_wrap": QFormLayout.RowWrapPolicy.DontWrapRows,
        "wrap_long": QFormLayout.RowWrapPolicy.WrapLongRows,
        "wrap_all": QFormLayout.RowWrapPolicy.WrapAllRows,
    }
    return mapping.get(value, QFormLayout.RowWrapPolicy.DontWrapRows)


def _get_field_growth_policy(value: FieldGrowthPolicy) -> QFormLayout.FieldGrowthPolicy:
    """Convert FieldGrowthPolicy string to Qt enum."""
    mapping: dict[FieldGrowthPolicy, QFormLayout.FieldGrowthPolicy] = {
        "fields_stay_at_size": QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint,
        "expanding_fields_grow": QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        "all_non_fixed_fields_grow": QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow,
    }
    return mapping.get(value, QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)


def apply_layout_config(
    layout: QLayout,
    layout_type: LayoutType,
    spacing: int | None = None,
    size_constraint: SizeConstraint | None = None,
    horizontal_spacing: int | None = None,
    vertical_spacing: int | None = None,
    row_wrap_policy: RowWrapPolicy | None = None,
    label_alignment: Qt.AlignmentFlag | None = None,
    form_alignment: Qt.AlignmentFlag | None = None,
    field_growth_policy: FieldGrowthPolicy | None = None,
) -> None:
    """Apply layout configuration settings.

    Args:
        layout: The Qt layout to configure.
        layout_type: The type of layout (for determining which settings apply).
        spacing: Universal spacing (setSpacing).
        size_constraint: Layout size constraint (setSizeConstraint).
        horizontal_spacing: Grid/Form horizontal spacing (setHorizontalSpacing).
        vertical_spacing: Grid/Form vertical spacing (setVerticalSpacing).
        row_wrap_policy: Form row wrap policy (setRowWrapPolicy).
        label_alignment: Form label alignment (setLabelAlignment).
        form_alignment: Form alignment (setFormAlignment).
        field_growth_policy: Form field growth policy (setFieldGrowthPolicy).
    """
    # Universal: spacing and size_constraint work on all layouts
    if spacing is not None:
        layout.setSpacing(spacing)

    if size_constraint is not None:
        layout.setSizeConstraint(_get_size_constraint(size_constraint))

    # Grid and Form: horizontal/vertical spacing
    if layout_type in ("grid", "form"):
        if horizontal_spacing is not None:
            if isinstance(layout, (QGridLayout, QFormLayout)):
                layout.setHorizontalSpacing(horizontal_spacing)
        if vertical_spacing is not None:
            if isinstance(layout, (QGridLayout, QFormLayout)):
                layout.setVerticalSpacing(vertical_spacing)

    # Form only settings
    if layout_type == "form" and isinstance(layout, QFormLayout):
        if row_wrap_policy is not None:
            layout.setRowWrapPolicy(_get_row_wrap_policy(row_wrap_policy))
        if label_alignment is not None:
            layout.setLabelAlignment(label_alignment)
        if form_alignment is not None:
            layout.setFormAlignment(form_alignment)
        if field_growth_policy is not None:
            layout.setFieldGrowthPolicy(_get_field_growth_policy(field_growth_policy))


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
