from dataclasses import MISSING, dataclass, fields
from typing import (
    Any,
    Callable,
    Literal,
    TypeVar,
    dataclass_transform,
    get_type_hints,
    overload,
)

from PySide6.QtWidgets import QBoxLayout, QFormLayout, QLayout, QWidget

from qtpie.factories.make import SIGNALS_METADATA_KEY
from qtpie.styles.style_class import QtStyleClass

T = TypeVar("T")


# Overload for @widget (no parens) - class passed directly
@overload
@dataclass_transform()
def widget(
    _cls: type[T],
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    layout: type[QLayout]
    | QBoxLayout.Direction
    | Literal["horizontal", "vertical", "form", "none"]
    | None = QBoxLayout.Direction.TopToBottom,
    add_widgets_to_layout: bool = True,
    width: int | None = None,
    height: int | None = None,
) -> type[T]: ...


# Overload for @widget() (with parens) - returns decorator
@overload
@dataclass_transform()
def widget(
    _cls: None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    layout: type[QLayout]
    | QBoxLayout.Direction
    | Literal["horizontal", "vertical", "form", "none"]
    | None = QBoxLayout.Direction.TopToBottom,
    add_widgets_to_layout: bool = True,
    width: int | None = None,
    height: int | None = None,
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform()
def widget(
    _cls: type[T] | None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    layout: type[QLayout]
    | QBoxLayout.Direction
    | Literal["horizontal", "vertical", "form", "none"]
    | None = QBoxLayout.Direction.TopToBottom,
    add_widgets_to_layout: bool = True,
    width: int | None = None,
    height: int | None = None,
) -> Callable[[type[T]], type[T]] | type[T]:
    def decorator(cls: type[T]) -> type[T]:
        # Always apply @dataclass to register this class's fields
        # (even if parent is already a dataclass)
        cls = dataclass(cls)

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Initialize QWidget first (it doesn't cooperate with super())
            QWidget.__init__(self)

            # Manually set dataclass fields with default_factory support
            for f in fields(cls):  # type: ignore[arg-type]
                if f.name in kwargs:
                    setattr(self, f.name, kwargs[f.name])
                elif f.default is not MISSING:
                    setattr(self, f.name, f.default)
                elif f.default_factory is not MISSING:
                    setattr(self, f.name, f.default_factory())

            # Connect signals from make() metadata
            # These are kwargs that had string or callable values - we check at runtime
            # if they're actually signals (have .connect method)
            for f in fields(cls):  # type: ignore[arg-type]
                potential_signals = f.metadata.get(SIGNALS_METADATA_KEY)
                if potential_signals:
                    widget_instance = getattr(self, f.name, None)
                    if widget_instance is not None:
                        for attr_name, handler in potential_signals.items():
                            attr = getattr(widget_instance, attr_name, None)
                            if attr is not None and hasattr(attr, "connect"):
                                # It's a signal - connect it
                                if isinstance(handler, str):
                                    # Look up method by name on self
                                    method = getattr(self, handler, None)
                                    if method is not None:
                                        attr.connect(method)
                                elif callable(handler):
                                    # Direct callable (lambda or function)
                                    attr.connect(handler)
                            else:
                                # Not a signal - it was a regular property, set it
                                # This handles cases like placeholderText="Name"
                                setter_name = (
                                    f"set{attr_name[0].upper()}{attr_name[1:]}"
                                )
                                setter = getattr(widget_instance, setter_name, None)
                                if setter is not None and callable(setter):
                                    setter(handler)
                                elif attr is not None:
                                    # Try direct assignment
                                    setattr(widget_instance, attr_name, handler)

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
                        if field.name.startswith("_") and not field.name.startswith(
                            "_stretch"
                        ):
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
                                        form_field_name_property = (
                                            widget_instance.property("form_field_name")
                                        )
                                        if isinstance(form_field_name_property, str):
                                            form_field_name = form_field_name_property
                                        elif widget_instance.objectName():
                                            form_field_name = (
                                                widget_instance.objectName()
                                            )
                                        if form_field_name:
                                            _layout.addRow(
                                                form_field_name, widget_instance
                                            )
                            elif issubclass(field_type, int) and field.name.startswith(
                                "_stretch"
                            ):
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
