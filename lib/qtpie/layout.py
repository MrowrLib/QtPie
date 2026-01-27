"""Layout configuration for QtPie widgets."""

from typing import Literal

# Layout type options
LayoutType = Literal["vertical", "horizontal", "form", "grid"] | None

# Grid position: (row, col) or (row, col, rowspan, colspan)
GridPosition = tuple[int, int] | tuple[int, int, int, int]


class Stretch:
    """Marker class for layout stretches.

    Adds stretch space to a layout using QBoxLayout.addStretch().
    Use in vertical/horizontal layouts to push widgets apart.

    Usage:
        @widget
        class MyWidget(Widget):
            _top: QLabel = new("Top")
            _stretch: Stretch = new()      # addStretch(1)
            _bottom: QLabel = new("Bottom")

        @widget
        class MyWidget(Widget):
            _left: QLabel = new("Left")
            _stretch: Stretch = new(3)     # addStretch(3) - higher factor
            _right: QLabel = new("Right")

        @widget
        class MyWidget(Widget):
            _nested: QHBoxLayout = new()
            _stretch_in_nested: Stretch = new(layout="_nested")  # Add to nested layout
    """

    pass


class Spacer:
    """Marker class for fixed-size layout spacing.

    Adds fixed pixel space to a layout using QBoxLayout.addSpacing(size).
    Unlike Stretch which expands, Spacer adds a fixed number of pixels.

    Usage:
        @widget
        class MyWidget(Widget):
            _top: QLabel = new("Top")
            _space: Spacer = new(20)       # addSpacing(20) - 20px fixed space
            _bottom: QLabel = new("Bottom")

        @widget
        class MyWidget(Widget):
            _nested: QHBoxLayout = new()
            _space_in_nested: Spacer = new(10, layout="_nested")  # Add to nested layout

    Note: The size argument is REQUIRED. Spacer = new() without a size is an error.
    """

    pass


# Layout configuration type aliases
# SizeConstraint maps to QLayout.SizeConstraint enum
SizeConstraint = Literal[
    "default",  # SetDefaultConstraint
    "fixed",  # SetFixedSize
    "minimum",  # SetMinimumSize
    "maximum",  # SetMaximumSize
    "min_max",  # SetMinAndMaxSize
    "no_constraint",  # SetNoConstraint
]

# RowWrapPolicy maps to QFormLayout.RowWrapPolicy enum
RowWrapPolicy = Literal[
    "dont_wrap",  # DontWrapRows
    "wrap_long",  # WrapLongRows
    "wrap_all",  # WrapAllRows
]

# FieldGrowthPolicy maps to QFormLayout.FieldGrowthPolicy enum
FieldGrowthPolicy = Literal[
    "fields_stay_at_size",  # FieldsStayAtSizeHint
    "expanding_fields_grow",  # ExpandingFieldsGrow
    "all_non_fixed_fields_grow",  # AllNonFixedFieldsGrow
]
