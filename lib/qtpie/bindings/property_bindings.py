"""Shared property binding utilities (visible=, enabled=, etc.)."""

from collections.abc import Callable
from typing import Any

from observant import Observable
from qtpy.QtCore import QObject

from qtpie.bindings.expression import create_expression_binding
from qtpie.bindings.format_binding import is_format_string
from qtpie.bindings.path import resolve_binding_source
from qtpie.bindings.setters import make_bound_setter
from qtpie.new_field import NewField
from qtpie.variable import Variable


def apply_property_bindings_for_fields(
    context: Any,
    fields: dict[str, NewField],
    get_target: Callable[[str], QObject | None],
    get_setter: Callable[[QObject, str], Callable[[Any], None] | None],
) -> None:
    """Apply property bindings (visible=, enabled=, etc.) for fields.

    This is a shared implementation used by Widget, Window, Menu, and App.

    Args:
        context: The context object (Widget, Window, Menu, or App instance) for resolving bindings.
        fields: Dictionary of field name to NewField.
        get_target: Function to get the target QObject for a field name.
        get_setter: Function to get the setter callable for a (target, prop_name) pair.
                    Should return None if the property is not bindable.
    """
    for field_name, field_info in fields.items():
        if not field_info.property_bindings:
            continue

        target = get_target(field_name)
        if target is None:
            continue

        for prop_name, bind_expr in field_info.property_bindings.items():
            prop_setter = get_setter(target, prop_name)
            if prop_setter is None:
                continue

            if is_format_string(bind_expr):
                # Expression binding like "{_count > 0}"
                create_expression_binding(context, bind_expr, prop_setter)
            else:
                # Simple variable reference like "_is_visible"
                source = resolve_binding_source(context, bind_expr)  # type: ignore[arg-type]
                if source is None:
                    continue

                if isinstance(source, Variable):
                    # Set initial value and subscribe
                    prop_setter(source.value)  # pyright: ignore[reportUnknownMemberType]
                    source.on_change(prop_setter)
                elif isinstance(source, Observable):
                    # Set initial value and subscribe
                    prop_setter(source.get())
                    source.on_change(prop_setter)


def get_widget_property_setter(widget: QObject, prop_name: str) -> Callable[[Any], None] | None:
    """Get a bound setter for a widget property using the binding registry.

    Args:
        widget: The widget to get the setter for.
        prop_name: The property name (e.g., "visible", "enabled").

    Returns:
        A callable that takes a value and sets the property, or None if not bindable.
    """
    from qtpie.bindings.registry import get_binding_registry

    registry = get_binding_registry()
    adapter = registry.get(widget, prop_name)
    if adapter is None or adapter.setter is None:
        return None

    return make_bound_setter(adapter.setter, widget)  # type: ignore[arg-type]


def get_action_property_setter(action: QObject, prop_name: str) -> Callable[[Any], None] | None:
    """Get a setter for a QAction property.

    Unlike widgets, QAction setters take only the value (not widget, value).

    Args:
        action: The QAction to get the setter for.
        prop_name: The property name (e.g., "enabled", "visible").

    Returns:
        A callable that takes a value and sets the property, or None if not found.
    """
    setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
    setter = getattr(action, setter_name, None)
    if setter is None or not callable(setter):
        return None

    # Return as-is since QAction setters take just the value
    return setter  # type: ignore[return-value]
