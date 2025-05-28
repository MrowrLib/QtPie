from __future__ import annotations

from dataclasses import dataclass

from qtpy.QtCore import QObject

from qtpie.factories.grid_position import GridPosition

WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME = "widgetFactoryProperties"


@dataclass(frozen=True)
class WidgetFactoryProperties:
    object_name: str | None = None
    class_names: list[str] | None = None
    form_field_label: str | None = None
    grid_position: GridPosition | None = None

    @staticmethod
    def set(object: QObject, properties: WidgetFactoryProperties) -> None:
        """Set the widget factory properties on a QObject."""
        object.setProperty(
            WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME,
            properties,
        )

    @staticmethod
    def get(object: QObject) -> WidgetFactoryProperties | None:
        """Get the widget factory properties from a QObject."""
        if object.property(WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME):
            return object.property(WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME)
        return None
