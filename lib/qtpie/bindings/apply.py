"""Shared binding application logic for Widget and Window."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from observant import Observable
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.new_field import NewField


class BindingConfig(Protocol):
    """Protocol for config objects that support bindings."""

    fields: dict[str, NewField]
    auto_bind: bool
    widget_props: dict[str, Any]


def apply_auto_bindings(
    host: QWidget,
    config: BindingConfig,
    *,
    create_expression_binding_fn: Callable[[Any, str, Callable[[Any], None]], None] | None = None,
) -> None:
    """Apply auto-bindings for QWidget fields.

    Works with both Widget and Window instances.

    Args:
        host: The Widget or Window instance
        config: Configuration with fields, auto_bind, etc.
        create_expression_binding_fn: Optional function to create expression bindings
    """
    from qtpie.bindings import bind, create_format_binding, is_format_string, resolve_binding_source
    from qtpie.variable import Variable as VarType

    for name, field_info in config.fields.items():
        # Skip list widget fields
        if field_info.is_list_widget:
            continue

        # Get the widget instance
        widget_instance = getattr(host, name, None)
        if widget_instance is None or not isinstance(widget_instance, QWidget):
            continue

        # Determine bind path
        if field_info.bind is not None:
            bind_path = field_info.bind
        elif config.auto_bind:
            bind_path = name.lstrip("_")
        else:
            continue

        # Handle format strings
        if is_format_string(bind_path):
            from qtpie.bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                setter = adapter.setter

                def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def setter_fn(val: Any) -> None:
                        s(w, val)

                    return setter_fn

                create_format_binding(host, bind_path, make_setter(setter, widget_instance))  # type: ignore[arg-type]
            continue

        # Resolve the binding source
        source = resolve_binding_source(host, bind_path)  # type: ignore[arg-type]
        if source is None:
            continue

        # Create the binding
        if isinstance(source, VarType):
            bind(source).to(widget_instance)
        elif isinstance(source, Observable):
            # Set up binding for Observable (e.g., from record field)
            from qtpie.bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                # Set initial value
                adapter.setter(widget_instance, source.get())

                # Subscribe to Observable changes
                setter = adapter.setter

                def make_obs_to_widget(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def on_observable_change(v: Any) -> None:
                        s(w, v)

                    return on_observable_change

                source.on_change(make_obs_to_widget(setter, widget_instance))

                # Two-way binding: Widget → Observable
                if adapter.signal_name is not None and adapter.getter is not None:
                    signal = getattr(widget_instance, adapter.signal_name, None)
                    getter = adapter.getter

                    def make_widget_to_obs(obs: Observable[Any], g: Callable[[Any], Any], w: QWidget) -> Callable[[], None]:
                        def on_widget_change() -> None:
                            obs.set(g(w))

                        return on_widget_change

                    if signal is not None:
                        signal.connect(make_widget_to_obs(source, getter, widget_instance))


def apply_property_bindings(
    host: QWidget,
    config: BindingConfig,
    *,
    create_expression_binding_fn: Callable[[Any, str, Callable[[Any], None]], None] | None = None,
) -> None:
    """Apply property bindings like visible="_is_visible" or enabled="{_count > 0}".

    Works with both Widget and Window instances.
    """
    from qtpie.bindings import is_format_string, resolve_binding_source
    from qtpie.bindings.registry import get_binding_registry
    from qtpie.variable import Variable as VarType

    registry = get_binding_registry()

    for name, field_info in config.fields.items():
        if not field_info.property_bindings:
            continue

        widget_instance = getattr(host, name, None)
        if widget_instance is None or not isinstance(widget_instance, QWidget):
            continue

        for prop_name, bind_expr in field_info.property_bindings.items():
            adapter = registry.get(widget_instance, prop_name)
            if adapter is None or adapter.setter is None:
                continue

            setter = adapter.setter

            def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                def setter_fn(val: Any) -> None:
                    s(w, val)

                return setter_fn

            prop_setter = make_setter(setter, widget_instance)

            if is_format_string(bind_expr):
                if create_expression_binding_fn is not None:
                    create_expression_binding_fn(host, bind_expr, prop_setter)
            else:
                source = resolve_binding_source(host, bind_expr)  # type: ignore[arg-type]
                if source is None:
                    continue

                if isinstance(source, VarType):
                    prop_setter(source.value)
                    source.on_change(prop_setter)
                elif isinstance(source, Observable):
                    prop_setter(source.get())
                    source.on_change(prop_setter)


def apply_reactive_widget_props(
    host: QWidget,
    config: BindingConfig,
) -> None:
    """Apply reactive widget properties from @widget/@window decorator.

    For props like windowTitle="{title}", creates a format binding.
    """
    from qtpie.bindings import create_format_binding, is_format_string

    for prop_name, value in config.widget_props.items():
        if not isinstance(value, str) or not is_format_string(value):
            continue

        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter_method = getattr(host, setter_name, None)
        if setter_method is None or not callable(setter_method):
            raise AttributeError(f"{type(host).__name__} has no setter '{setter_name}' for property '{prop_name}'")

        create_format_binding(host, value, setter_method)  # type: ignore[arg-type]
