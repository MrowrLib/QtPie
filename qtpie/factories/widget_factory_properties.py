from dataclasses import dataclass


@dataclass(frozen=True)
class WidgetFactoryProperties:
    object_name: str | None = None
    class_names: list[str] | None = None
    form_field_label: str | None = None
    grid_position: tuple[int, int] | None = None
