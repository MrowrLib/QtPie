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
