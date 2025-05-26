from typing import Callable, ParamSpec, TypeVar, cast

from qtpy.QtCore import QObject

from qtpie.factories.widget_factory_properties import WidgetFactoryProperties

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

    instance = widget_type(*args, **kwargs)

    if isinstance(instance, QObject):
        instance.setProperty(
            "widgetFactoryProperties",
            WidgetFactoryProperties(
                object_name=object_name,
                class_names=class_names,
            ),
        )

    return instance
