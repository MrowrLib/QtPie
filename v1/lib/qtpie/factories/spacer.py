"""The spacer() factory function for adding spacers to box layouts."""

from dataclasses import dataclass, field
from typing import Any

from qtpy.QtWidgets import QSpacerItem

# Metadata key used to store spacer info for the @widget decorator
SPACER_METADATA_KEY = "qtpie_spacer"


@dataclass(frozen=True)
class SpacerConfig:
    """Configuration for a spacer in a box layout.

    Attributes:
        factor: Stretch factor (0 = fixed spacer, >0 = proportional stretch).
        min_size: Minimum size in pixels (for the layout direction).
        max_size: Maximum size in pixels (for the layout direction).
    """

    factor: int = 0
    min_size: int = 0
    max_size: int = 0


def spacer(
    factor: int = 0,
    *,
    min_size: int = 0,
    max_size: int = 0,
) -> QSpacerItem:
    """
    Create a spacer for box layouts.

    Args:
        factor: Stretch factor. 0 means a fixed spacer, values >0 determine
                proportional stretching relative to other spacer items.
        min_size: Minimum size in pixels (in the layout direction).
        max_size: Maximum size in pixels (in the layout direction). Use 0 for unlimited.

    Examples:
        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            header: QLabel = make(QLabel, "Header")
            spacer1: QSpacerItem = spacer(1)           # proportional stretch
            content: QLabel = make(QLabel, "Content")
            spacer2: QSpacerItem = spacer()            # minimal spacer
            footer: QLabel = make(QLabel, "Footer")

        # With size constraints
        @widget(layout="horizontal")
        class MyWidget(QWidget, Widget):
            left: QLabel = make(QLabel, "Left")
            gap: QSpacerItem = spacer(min_size=20)     # at least 20px gap
            right: QLabel = make(QLabel, "Right")

        # Fixed size spacer
        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            gap: QSpacerItem = spacer(min_size=50, max_size=50)  # exactly 50px
            bottom: QLabel = make(QLabel, "Bottom")

    Returns:
        At type-check time: QSpacerItem
        At runtime: a dataclass field that creates QSpacerItem with the config

    Note:
        - Do NOT use underscore prefix - underscore fields are completely ignored
        - Spacer fields are only processed in box layouts (vertical/horizontal)
        - They are ignored in form and grid layouts
        - The actual QSpacerItem is stored on the instance for later access
    """
    spacer_config = SpacerConfig(factor=factor, min_size=min_size, max_size=max_size)

    # Store the config in metadata for the widget decorator to process
    metadata: dict[str, Any] = {SPACER_METADATA_KEY: spacer_config}

    # We use init=False because the widget decorator will create and assign the spacer
    return field(init=False, default=None, metadata=metadata)  # type: ignore[return-value]
