from dataclasses import MISSING, Field, dataclass, field
from typing import Any, Callable, ParamSpec, TypeVar, cast

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QLabel, QWidget

T = TypeVar("T", covariant=True)
P = ParamSpec("P")

# note: could use field metadata to store options


@dataclass(frozen=True)
class WidgetFactoryOptions:
    object_name: str | None = None
    class_names: list[str] | None = None
    form_field_label: str | None = None
    grid_position: tuple[int, int] | None = None


def make(class_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    def factory_fn() -> T:
        return class_type(*args, **kwargs)

    return field(default_factory=factory_fn)


def form_row(label: str, class_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    def factory_fn() -> T:
        widget = class_type(*args, **kwargs)
        if isinstance(widget, QObject):
            widget.setProperty("_widget_factory_options", WidgetFactoryOptions(form_field_label=label))
        return widget

    return field(default_factory=factory_fn)


def grid_item(position: tuple[int, int], class_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    def factory_fn() -> T:
        widget = class_type(*args, **kwargs)
        if isinstance(widget, QObject):
            widget.setProperty("_widget_factory_options", WidgetFactoryOptions(grid_position=position))
        return widget

    return field(default_factory=factory_fn)


# def meta(id: str, ... what we're given is a field() although statically probably typed as a T ?


H = TypeVar("H")


def _with_meta_base(base_field: Field[H], *args: Any, **kwargs: Any) -> H:
    factory = cast(Callable[[], H], base_field.default_factory)

    return field(
        default_factory=factory,
        init=base_field.init,
        repr=base_field.repr,
        hash=base_field.hash,
        compare=base_field.compare,
        metadata={**(base_field.metadata or {}), **kwargs},
    )


def with_meta(base_field: H, *args: Any, **kwargs: Any) -> H:
    """
    Wraps a field(...) return (statically typed as T), adds metadata.
    Assumes T is actually a dataclasses.Field at runtime.
    """
    assert isinstance(base_field, Field), "meta() expects a dataclass field"
    assert base_field.default_factory is not MISSING, "field must have a default_factory"

    return _with_meta_base(cast(Field[H], base_field), *args, **kwargs)


def specific_meta(id: str | None = None, classes: list[str] | None = None, field: H | None = None, *args: Any, **kwargs: Any) -> H:
    field_value: Field[H] | None = None
    if field is not None:
        assert isinstance(field, Field), "specific_meta() expects a dataclass field"
        field_value = cast(Field[H], field)
    elif len(args) == 1 and isinstance(args[0], Field):
        if isinstance(args[0].default_factory, Callable):
            field_value = cast(Field[H], args[0])

    assert field_value is not None, "specific_meta() requires a dataclass field or a single Field argument"

    return _with_meta_base(field_value, id=id, classes=classes, **kwargs)


@dataclass
class SimpleDataclassWidget(QWidget):
    # Regular field() factory for widgets when using QBoxLayout (QVBoxLayout, QHBoxLayout)
    label1: QLabel = make(QLabel, "Hello, World!")
    label2: QLabel = make(QLabel, "This is a QLabel in a dataclass widget")

    # But the QFormLayout requires a different approach
    form_item1: QLabel = form_row("Form Label", QLabel, "This is a QLabel in a form row")
    form_item2: QLabel = form_row("Another Form Label", QLabel, "This is another QLabel in a form row")

    # For QGridLayout, we can use grid_item
    grid_item1: QLabel = grid_item((0, 0), QLabel, "This is a QLabel in a grid item")
    grid_item2: QLabel = grid_item((1, 0), QLabel, "This is another QLabel in a grid item")

    # Let's make a wrapping/decorator-ish function which can add metadata to any of these ^
    #
    # This one uses kwargs, which means that the fields must be provided a
    item_with_metadata: QLabel = with_meta(make(QLabel, "This QLabel has metadata"), id="unique_id_123")
    #
    #
    # This one supports specific metadata and lets you use either kwargs...
    item_with_specific_metadata: QLabel = specific_meta(
        id="unique_id_456",
        classes=["class1", "class2"],
        field=make(QLabel, "This QLabel has specific metadata"),
    )
    # or positional arguments
    item_with_positional_metadata: QLabel = specific_meta(
        "unique_id_789",
        ["class3", "class4"],
        make(QLabel, "This QLabel has positional metadata"),
    )
