"""Layout configuration for QtPie widgets."""

from typing import Literal

# Layout type options
LayoutType = Literal["vertical", "horizontal", "form", "grid"] | None

# Grid position: (row, col) or (row, col, rowspan, colspan)
GridPosition = tuple[int, int] | tuple[int, int, int, int]
