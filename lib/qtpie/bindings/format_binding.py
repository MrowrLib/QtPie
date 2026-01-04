"""Format string binding support."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableProxy

from .path import BindingSource, resolve_binding_source

if TYPE_CHECKING:
    from qtpie.widget import Widget


def is_format_string(template: str) -> bool:
    """Check if a string is a format template with {field} placeholders."""
    return "{" in template and "}" in template


def parse_format_string(template: str) -> list[str]:
    """Parse a format string and return the list of field paths.

    Args:
        template: Format string like '{name}, age {age}'

    Returns:
        List of field paths: ['name', 'age']
    """
    pattern = r"\{([^}]+)\}"
    return re.findall(pattern, template)


def format_with_values(template: str, values: dict[str, Any]) -> str:
    """Format a template string with the given values.

    Args:
        template: Format string like '{name}, age {age}'
        values: Dict mapping field paths to values

    Returns:
        Formatted string with values substituted
    """
    result = template
    for field, value in values.items():
        placeholder = f"{{{field}}}"
        result = result.replace(placeholder, str(value) if value is not None else "")
    return result


def get_observable_value(source: BindingSource) -> Any:
    """Get the current value from a binding source."""
    from qtpie.variable import Variable

    if isinstance(source, Variable):
        return source.value
    elif isinstance(source, Observable):
        return source.get()
    elif isinstance(source, ObservableProxy):
        return source.unwrap()
    return None


def get_static_value(widget: Widget[Any], path: str) -> Any:
    """Try to get a static (non-reactive) attribute value.

    Handles paths like 'title' or nested paths like 'config.name'.
    """
    lookup_path = path.lstrip("_")
    parts = lookup_path.split(".")

    current: Any = widget
    for part in parts:
        # Try with underscore prefix first
        if hasattr(current, f"_{part}"):
            current = getattr(current, f"_{part}")
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current


def create_format_binding(
    widget: Widget[Any],
    template: str,
    setter: Any,
) -> None:
    """Create a format string binding that updates when any field changes.

    Supports both reactive sources (Variable, Observable) and static attributes.
    Static attributes are re-read whenever any reactive field changes.

    Args:
        widget: The Widget instance to resolve paths from.
        template: Format string like '{name}, age {age}'.
        setter: Callable to set the formatted value (e.g., label.setText).
    """
    fields = parse_format_string(template)

    # Resolve all field sources (reactive)
    sources: dict[str, BindingSource] = {}
    static_fields: list[str] = []

    for field in fields:
        source = resolve_binding_source(widget, field)
        if source is not None:
            sources[field] = source
        else:
            # Not a reactive source - treat as static attribute
            static_fields.append(field)

    def update_value() -> None:
        """Recompute and set the formatted value."""
        values: dict[str, Any] = {}

        # Get reactive values
        for field, source in sources.items():
            values[field] = get_observable_value(source)

        # Get static values (re-read each time)
        for field in static_fields:
            values[field] = get_static_value(widget, field)

        formatted = format_with_values(template, values)
        setter(formatted)

    # Set initial value
    update_value()

    # Subscribe to all reactive sources
    for source in sources.values():
        if isinstance(source, Observable):
            source.on_change(lambda _: update_value())
        elif isinstance(source, ObservableProxy):
            source.on_change(update_value)
        else:
            # Variable - subscribe to its observable
            from qtpie.variable import Variable

            if isinstance(source, Variable):

                def var_callback(_v: Any) -> None:
                    update_value()

                source.on_change(var_callback)
