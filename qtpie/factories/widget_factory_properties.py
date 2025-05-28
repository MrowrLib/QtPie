from dataclasses import dataclass

from qtpie.factories.grid_position import GridPosition


@dataclass(frozen=True)
class WidgetFactoryProperties:
    object_name: str | None = None
    class_names: list[str] | None = None
    form_field_label: str | None = None
    grid_position: GridPosition | None = None
