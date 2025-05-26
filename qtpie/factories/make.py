from dataclasses import dataclass, field
from typing import Callable, ParamSpec, TypeVar, cast

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QLabel

from qtpie.factories.widget_factory_details import WidgetFactoryDetails

T = TypeVar("T", covariant=True)
P = ParamSpec("P")


def make(widget_type_info: Callable[P, T] | tuple[Callable[P, T], str | list[str]] | tuple[Callable[P, T], str, list[str]], *args: P.args, **kwargs: P.kwargs) -> T:
    widget_type: Callable[P, T]
    object_name: str | None = None
    class_names: list[str] = []

    if isinstance(widget_type_info, tuple):
        typed_tuple = cast(tuple[Callable[P, T], str | list[str], list[str] | None], widget_type_info)

        widget_type = typed_tuple[0]

        id_or_class_list = typed_tuple[1]
        if isinstance(id_or_class_list, str):
            object_name = id_or_class_list
        else:
            class_names.extend(id_or_class_list)

        if len(typed_tuple) > 2:
            class_names.extend(typed_tuple[2] or [])

    else:
        widget_type = widget_type_info

    def factory_fn() -> T:
        widget = widget_type(*args, **kwargs)
        return widget

    return field(
        default_factory=factory_fn,
        metadata={
            "widget_factory_details": WidgetFactoryDetails(
                object_name=object_name,
                class_names=class_names,
            )
        },
    )


@dataclass
class ExampleClassWithWidgetAttributes:
    label: QLabel = make(QLabel, text="Hello, World! I am a constructor argument to QLabel.")

    # Or if you wanna just make it and declare an object name:
    label_with_name: QLabel = make((QLabel, "the-object-name"), "Hello, World! I am a constructor argument to QLabel.")

    # Or maybe you wanna set some class names:
    label_with_class_names: QLabel = make((QLabel, ["class1", "class2"]), "Hello, World! I am a constructor argument to QLabel.")

    # Or you can do both:
    label_with_both: QLabel = make((QLabel, "the-object-name", ["class1", "class2"]), "Hello, World! I am a constructor argument to QLabel.")


def _make(widget_type_info: Callable[P, T] | tuple[Callable[P, T], str | list[str]] | tuple[Callable[P, T], str, list[str]], *args: P.args, **kwargs: P.kwargs) -> T:
    widget_type: Callable[P, T]
    object_name: str | None = None
    class_names: list[str] = []

    if isinstance(widget_type_info, tuple):
        typed_tuple = cast(tuple[Callable[P, T], str | list[str], list[str] | None], widget_type_info)

        widget_type = typed_tuple[0]

        id_or_class_list = typed_tuple[1]
        if isinstance(id_or_class_list, str):
            object_name = id_or_class_list
        else:
            class_names.extend(id_or_class_list)

        if len(typed_tuple) > 2:
            class_names.extend(typed_tuple[2] or [])

    else:
        widget_type = widget_type_info

    instance = widget_type(*args, **kwargs)

    if isinstance(instance, QObject):
        if object_name is not None:
            instance.setObjectName(object_name)
        if class_names:
            instance.setProperty("classNames", class_names)

    return instance


# Example usage:


class ExampleThatIsNotADataClass:
    label: QLabel
    label_with_name: QLabel
    label_with_class_names: QLabel
    label_with_both: QLabel

    # If we make it IWidget.make() then we can call self.make() and we could optionally have
    # it have the ability to add to tha layout() even AFTER construction.

    def __init__(self):
        self.label = _make(QLabel, "Hello, World! I am a constructor argument to QLabel.")
        self.label_with_name = _make((QLabel, "the-object-name"), "Hello, World! I am a constructor argument to QLabel.")
        self.label_with_class_names = _make((QLabel, ["class1", "class2"]), "Hello, World! I am a constructor argument to QLabel.")
        self.label_with_both = _make((QLabel, "the-object-name", ["class1", "class2"]), "Hello, World! I am a constructor argument to QLabel.")
