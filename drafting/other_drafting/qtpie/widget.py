from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Callable, Literal, TypeVar, dataclass_transform, get_type_hints

from PySide6.QtWidgets import QBoxLayout, QFormLayout, QLayout, QWidget

from qtpie.styles import QtStyleClass

T = TypeVar("T", bound=QWidget)


@dataclass_transform()
def widget(
    _cls: type[T] | None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    layout: type[QLayout] | QBoxLayout.Direction | Literal["horizontal", "vertical", "form", "none"] | None = QBoxLayout.Direction.TopToBottom,
    add_widgets_to_layout: bool = True,
    width: int | None = None,
    height: int | None = None,
) -> Callable[[type[T]], type[T]] | type[T]:
    def decorator(cls: type[T]) -> type[T]:
        if not is_dataclass(cls):
            cls = dataclass(cls)

        original_init = cls.__init__

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)  # ✅ dataclass sets fields
            super(type(self), self).__init__()  # ✅ Qt base initialized (NO kwargs!)

            if name:
                self.setObjectName(name)
            elif not self.objectName():
                object_name = cls.__name__

                # if it ends with "Widget", remove it
                if object_name.endswith("Widget"):
                    object_name = object_name[:-6]

                self.setObjectName(object_name)

            if classes:
                QtStyleClass.set_classes(self, classes)
            if width is not None:
                self.setFixedWidth(width)
            if height is not None:
                self.setFixedHeight(height)

            if layout == "form" or layout == QFormLayout:
                QtStyleClass.add_class(self, "form")

            _layout: QLayout | None = None
            _box_layout: QBoxLayout | None = None
            _layout_direction: QBoxLayout.Direction | None = None

            if layout is not None:
                if isinstance(layout, str):
                    if layout.lower() == "horizontal":
                        _layout_direction = QBoxLayout.Direction.LeftToRight
                    elif layout.lower() == "vertical":
                        _layout_direction = QBoxLayout.Direction.TopToBottom
                    elif layout.lower() == "form":
                        _layout = QFormLayout()
                    elif layout.lower() == "none":
                        _layout = None
                    else:
                        _layout_direction = QBoxLayout.Direction.TopToBottom
                elif isinstance(layout, type):
                    _layout = layout()
                else:
                    _layout_direction = layout

                if _layout is None and _layout_direction is not None:
                    _box_layout = QBoxLayout(_layout_direction)
                    _layout = _box_layout

                if _layout is not None:
                    self.setLayout(_layout)

                if add_widgets_to_layout:
                    type_hints = get_type_hints(self.__class__)
                    for field in fields(self.__class__):
                        if field.name.startswith("_") and not field.name.startswith("_stretch"):
                            continue

                        field_type = type_hints.get(field.name)
                        if isinstance(field_type, type):
                            if issubclass(field_type, QWidget):
                                widget_instance = getattr(self, field.name, None)
                                if isinstance(widget_instance, QWidget):
                                    if _box_layout is not None:
                                        _box_layout.addWidget(widget_instance)
                                    elif isinstance(_layout, QFormLayout):
                                        form_field_name: str | None = None
                                        form_field_name_property = widget_instance.property("form_field_name")
                                        if isinstance(form_field_name_property, str):
                                            form_field_name = form_field_name_property
                                        elif widget_instance.objectName():
                                            form_field_name = widget_instance.objectName()
                                        if form_field_name:
                                            _layout.addRow(form_field_name, widget_instance)
                            elif issubclass(field_type, int) and field.name.startswith("_stretch"):
                                stretch = getattr(self, field.name, 0)
                                if _box_layout is not None:
                                    _box_layout.addStretch(stretch)

            self.setup()
            self.setup_values()
            self.setup_bindings()
            if self.layout() is not None:
                self.setup_layout(self.layout())
            if isinstance(self.layout(), QBoxLayout):
                self.setup_box_layout(self.layout())
            self.setup_styles()
            self.setup_events()
            self.setup_signals()

        cls.__init__ = new_init
        return cls

    if _cls is not None:
        return decorator(_cls)
    return decorator
