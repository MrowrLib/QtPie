"""Format string binding support with Python expression evaluation."""

from __future__ import annotations

import ast
import string
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableProxy

from .path import BindingSource, resolve_binding_source

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.widget import Widget


def is_format_string(template: str) -> bool:
    """Check if a string is a format template with {field} placeholders."""
    return "{" in template and "}" in template


# Python builtins that shouldn't be treated as widget attributes
_BUILTINS = frozenset(
    {
        "len",
        "str",
        "int",
        "float",
        "bool",
        "abs",
        "min",
        "max",
        "sum",
        "round",
        "sorted",
        "list",
        "dict",
        "set",
        "tuple",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "any",
        "all",
        "True",
        "False",
        "None",
        "repr",
        "type",
        "isinstance",
        "hasattr",
        "getattr",
        "ord",
        "chr",
        "hex",
        "bin",
        "oct",
    }
)


def _is_simple_name(expr: str) -> bool:
    """Check if expression is a simple name or dotted path (no operators/calls)."""
    # Simple name: "count" or "dog.name" or "#self"
    if expr.startswith("#"):
        return True
    normalized = expr.replace("?.", ".")
    return all(part.isidentifier() for part in normalized.split("."))


def _extract_ast_names(expr: str) -> set[str]:
    """Extract all variable names from a Python expression using AST.

    Only returns top-level names (for 'dog.name', returns 'dog').

    Example: "count + 5" → {"count"}
    Example: "dog.name.upper()" → {"dog"}
    Example: "x + y * z" → {"x", "y", "z"}
    Example: "len(name)" → {"name"}
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


class _FormatField:
    """A parsed field from a format string."""

    __slots__ = ("expression", "format_spec", "is_expression")

    def __init__(self, expression: str, format_spec: str, is_expression: bool) -> None:
        self.expression = expression
        self.format_spec = format_spec
        self.is_expression = is_expression


def _parse_format_fields(format_string: str) -> list[_FormatField]:
    """Extract fields from a format string using string.Formatter.

    Example: "Count: {count}" → [_FormatField("count", "", False)]
    Example: "{price * 1.1:.2f}" → [_FormatField("price * 1.1", ".2f", True)]
    Example: "{name.upper()}" → [_FormatField("name.upper()", "", True)]
    """
    formatter = string.Formatter()
    fields: list[_FormatField] = []
    for _, field_name, format_spec, _ in formatter.parse(format_string):
        if field_name is not None and field_name != "":
            is_expr = not _is_simple_name(field_name)
            fields.append(_FormatField(field_name, format_spec or "", is_expr))
    return fields


def _get_variable_names(fields: list[_FormatField]) -> set[str]:
    """Extract all variable names/paths from format fields.

    For simple names like 'count' or 'dog.name', returns the full path.
    For expressions like 'count + 5', uses AST to find all root names.
    Filters out Python builtins and special placeholders (#self).
    """
    names: set[str] = set()
    for field in fields:
        if field.is_expression:
            # Use AST to extract names from expression
            expr_names = _extract_ast_names(field.expression)
            names.update(expr_names - _BUILTINS)
        else:
            # Simple name or dotted path
            expr = field.expression
            if expr.startswith("#"):
                # Special placeholder like #self - skip for name collection
                continue
            normalized = expr.replace("?.", ".")
            root = normalized.split(".")[0]
            if root not in _BUILTINS:
                names.add(normalized)
    return names


def _get_observables_for_name(widget: Widget[Any], name: str) -> list[Observable[Any]]:
    """Get observables for a variable name (may be nested path).

    Returns a list of observables to subscribe to.
    """
    from qtpie.variable import Variable

    result: list[Observable[Any]] = []

    # Try to resolve as binding source
    source = resolve_binding_source(widget, name)
    if source is not None:
        if isinstance(source, Variable):
            obs = source.observable
            if isinstance(obs, Observable):
                result.append(obs)
            elif isinstance(obs, ObservableProxy):
                # Subscribe to proxy changes
                # ObservableProxy doesn't directly fit Observable[Any], skip for now
                pass
        elif isinstance(source, Observable):
            result.append(source)
        elif isinstance(source, ObservableProxy):
            # For nested paths, the proxy field observable is what we want
            pass

    return result


def _get_root_names(names: set[str]) -> set[str]:
    """Get root variable names for building eval context.

    "dog.name" → "dog"
    "simple" → "simple"
    """
    roots: set[str] = set()
    for name in names:
        root = name.split(".")[0]
        roots.add(root)
    return roots


def create_format_binding(
    widget: Widget[Any],
    template: str,
    setter: Callable[[Any], None],
    *,
    variable: BindingSource | None = None,
) -> None:
    """Create a format string binding that updates when any field changes.

    Supports complex Python expressions:
    - Simple fields: {name}, {dog.name}
    - Function calls: {len(name)}, {name.upper()}
    - Math: {(x + y) * z}
    - Method calls: {compute_something()}
    - Special placeholders:
      - {#self} - the variable's value (if variable provided) or widget instance
      - {#var} - alias for variable's value (only when variable provided)
      - {#widget} - always the widget/window instance
      - {#window} - alias for #widget (more semantic for Window classes)

    Args:
        widget: The Widget instance to resolve paths from.
        template: Format string like '{name}, age {age}' or '{len(name)}'.
        setter: Callable to set the formatted value (e.g., label.setText).
        variable: Optional Variable/Observable to use for #self/#var resolution.
    """
    from qtpie.variable import Variable

    fields = _parse_format_fields(template)
    if not fields:
        return

    # Extract all variable names/paths we need to observe
    var_names = _get_variable_names(fields)

    # Check for special placeholder usage (can appear anywhere in expression)
    uses_self = any("#self" in f.expression for f in fields)
    uses_var = any("#var" in f.expression for f in fields)
    uses_widget = any("#widget" in f.expression or "#window" in f.expression for f in fields)

    # Get ROOT names for building eval context
    root_names = _get_root_names(var_names)

    # Collect all observables to subscribe to
    all_observables: list[Observable[Any]] = []

    for name in var_names:
        obs_list = _get_observables_for_name(widget, name)
        all_observables.extend(obs_list)

    # If we have a variable, subscribe to it too
    if variable is not None:
        if isinstance(variable, Variable):
            obs = variable.observable
            if isinstance(obs, Observable):
                all_observables.append(obs)
        elif isinstance(variable, Observable):
            all_observables.append(variable)

    # Build the compute function
    def compute() -> str:
        # Build context with current values using root names
        context: dict[str, Any] = {}

        # Add #widget as 'widget_ref' in context if used
        if uses_widget:
            context["widget_ref"] = widget

        # Add #self - if variable provided, it's the variable's value; otherwise widget
        if uses_self:
            if variable is not None:
                context["self"] = get_observable_value(variable)
            else:
                context["self"] = widget

        # Add #var - always the variable's value (only valid when variable provided)
        if uses_var and variable is not None:
            context["var"] = get_observable_value(variable)

        # Add all variable values to context using root names
        for root_name in root_names:
            # Try with underscore prefix first, then without
            for attr_name in [f"_{root_name}", root_name]:
                if hasattr(widget, attr_name):
                    raw_attr: Any = getattr(widget, attr_name)
                    if isinstance(raw_attr, Variable):
                        context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                    else:
                        context[root_name] = raw_attr
                    break

        # Also add record fields if Widget[T]
        if hasattr(widget, "_qtpie_config"):
            config = widget._qtpie_config  # pyright: ignore[reportPrivateUsage]
            if config.record_type is not None:
                try:
                    record = widget.record
                    for root_name in root_names:
                        if root_name not in context and hasattr(record.observable, root_name):
                            obs = getattr(record.observable, root_name)
                            if isinstance(obs, Observable):
                                context[root_name] = obs.get()
                except (TypeError, AttributeError):
                    pass

        # Process each field and build the result
        result_parts: list[str] = []

        formatter = string.Formatter()
        for literal_text, field_name, format_spec, _ in formatter.parse(template):
            result_parts.append(literal_text)

            if field_name is not None and field_name != "":
                # Handle special # placeholders - replace all occurrences
                eval_expr = field_name
                eval_expr = eval_expr.replace("#self", "self")
                eval_expr = eval_expr.replace("#var", "var")
                eval_expr = eval_expr.replace("#widget", "widget_ref")
                eval_expr = eval_expr.replace("#window", "widget_ref")

                # Evaluate the expression
                try:
                    value = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                    # If value is callable (method without parens), call it
                    if callable(value) and not isinstance(value, type):
                        value = value()
                except Exception:
                    value = f"<error: {field_name}>"

                # Apply format spec if present
                if format_spec:
                    try:
                        value = format(value, format_spec)
                    except Exception:
                        value = str(value)
                else:
                    value = str(value)

                result_parts.append(value)

        return "".join(result_parts)

    # Set initial value
    setter(compute())

    # Subscribe to ALL observables - when any changes, recompute
    def on_any_change(_: Any) -> None:
        setter(compute())

    for obs in all_observables:
        obs.on_change(on_any_change)


# Legacy functions for backwards compatibility
def parse_format_string(template: str) -> list[str]:
    """Parse a format string and return the list of field paths.

    Args:
        template: Format string like '{name}, age {age}'

    Returns:
        List of field paths: ['name', 'age']
    """
    fields = _parse_format_fields(template)
    return [f.expression for f in fields]


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
