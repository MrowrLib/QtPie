"""Format string binding support with Python expression evaluation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet

from .path import BindingSource, resolve_binding_source

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.widget import Widget
    from qtpie.window import Window


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
    """Extract fields from a format string with balanced brace parsing.

    This custom parser handles complex Python expressions including those with
    string literals containing special characters like '!' that would confuse
    Python's string.Formatter.

    Example: "Count: {count}" → [_FormatField("count", "", False)]
    Example: "{price * 1.1:.2f}" → [_FormatField("price * 1.1", ".2f", True)]
    Example: "{name.upper()}" → [_FormatField("name.upper()", "", True)]
    Example: "{'Yes!' if x else 'No'}" → [_FormatField("'Yes!' if x else 'No'", "", True)]
    """
    fields: list[_FormatField] = []
    i = 0
    n = len(format_string)

    while i < n:
        # Find next '{' that isn't escaped (not '{{')
        if format_string[i] == "{":
            if i + 1 < n and format_string[i + 1] == "{":
                # Escaped brace, skip both
                i += 2
                continue

            # Start of a field - find the matching '}'
            start = i + 1
            brace_depth = 1
            in_string: str | None = None  # Track if we're inside a string literal
            j = start

            while j < n and brace_depth > 0:
                ch = format_string[j]

                # Handle string literals
                if in_string is None:
                    if ch in ("'", '"'):
                        # Check for triple quotes
                        if j + 2 < n and format_string[j : j + 3] in ('"""', "'''"):
                            in_string = format_string[j : j + 3]
                            j += 3
                            continue
                        else:
                            in_string = ch
                            j += 1
                            continue
                    elif ch == "{":
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            break
                else:
                    # Inside a string - look for the closing quote
                    if len(in_string) == 3:
                        # Triple-quoted string
                        if format_string[j : j + 3] == in_string:
                            in_string = None
                            j += 3
                            continue
                    else:
                        # Single-quoted string - handle escapes
                        if ch == "\\":
                            j += 2  # Skip escape sequence
                            continue
                        elif ch == in_string:
                            in_string = None

                j += 1

            if brace_depth == 0:
                # Found matching brace - extract field content
                field_content = format_string[start:j]

                # Now parse for format spec - find ':' that's not inside expression
                expr, format_spec = _split_field_content(field_content)

                if expr:
                    is_expr = not _is_simple_name(expr)
                    fields.append(_FormatField(expr, format_spec, is_expr))

                i = j + 1
            else:
                # Unmatched brace, skip it
                i += 1
        else:
            i += 1

    return fields


def _parse_format_template(format_string: str) -> list[tuple[str, _FormatField | None]]:
    """Parse format string into literal text and field pairs.

    Returns a list of (literal_text, field) tuples where field may be None
    for trailing literal text. This is similar to string.Formatter.parse()
    but handles complex Python expressions properly.

    Example: "Count: {count}" → [("Count: ", field), ("", None)]
    Example: "{'Yes!' if x else 'No'}" → [("", field), ("", None)]
    """
    result: list[tuple[str, _FormatField | None]] = []
    i = 0
    n = len(format_string)
    literal_start = 0

    while i < n:
        if format_string[i] == "{":
            if i + 1 < n and format_string[i + 1] == "{":
                # Escaped brace - include one brace in literal
                # We'll handle this by including up to i, then skip one brace
                i += 2
                continue

            # Found field start - capture literal text before it
            literal_text = format_string[literal_start:i]
            # Handle escaped braces in literal
            literal_text = literal_text.replace("{{", "{").replace("}}", "}")

            # Find matching brace
            start = i + 1
            brace_depth = 1
            in_string: str | None = None
            j = start

            while j < n and brace_depth > 0:
                ch = format_string[j]

                if in_string is None:
                    if ch in ("'", '"'):
                        if j + 2 < n and format_string[j : j + 3] in ('"""', "'''"):
                            in_string = format_string[j : j + 3]
                            j += 3
                            continue
                        else:
                            in_string = ch
                            j += 1
                            continue
                    elif ch == "{":
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            break
                else:
                    if len(in_string) == 3:
                        if format_string[j : j + 3] == in_string:
                            in_string = None
                            j += 3
                            continue
                    else:
                        if ch == "\\":
                            j += 2
                            continue
                        elif ch == in_string:
                            in_string = None

                j += 1

            if brace_depth == 0:
                field_content = format_string[start:j]
                expr, format_spec = _split_field_content(field_content)

                if expr:
                    is_expr = not _is_simple_name(expr)
                    field = _FormatField(expr, format_spec, is_expr)
                    result.append((literal_text, field))
                else:
                    # Empty field like {} - just add literal
                    result.append((literal_text, None))

                i = j + 1
                literal_start = i
            else:
                i += 1
        else:
            i += 1

    # Add any remaining literal text
    if literal_start < n:
        remaining = format_string[literal_start:]
        remaining = remaining.replace("{{", "{").replace("}}", "}")
        result.append((remaining, None))
    elif not result or result[-1][1] is not None:
        # Ensure we have a trailing entry for consistency
        result.append(("", None))

    return result


def _split_field_content(content: str) -> tuple[str, str]:
    """Split field content into expression and format spec.

    The format spec follows a ':' that is not inside parens, brackets, braces, or strings.
    Example: "price * 1.1:.2f" → ("price * 1.1", ".2f")
    Example: "'Hello'" → ("'Hello'", "")
    Example: "d['key']" → ("d['key']", "")
    """
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    in_string: str | None = None
    i = 0
    n = len(content)

    while i < n:
        ch = content[i]

        # Handle string literals
        if in_string is None:
            if ch in ("'", '"'):
                if i + 2 < n and content[i : i + 3] in ('"""', "'''"):
                    in_string = content[i : i + 3]
                    i += 3
                    continue
                else:
                    in_string = ch
                    i += 1
                    continue
            elif ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth -= 1
            elif ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth -= 1
            elif ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
            elif ch == ":" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                # Found format spec separator
                return content[:i], content[i + 1 :]
        else:
            # Inside string
            if len(in_string) == 3:
                if content[i : i + 3] == in_string:
                    in_string = None
                    i += 3
                    continue
            else:
                if ch == "\\":
                    i += 2
                    continue
                elif ch == in_string:
                    in_string = None

        i += 1

    # No format spec found
    return content, ""


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


def _get_observables_for_name(widget: Widget[Any] | Window[Any], name: str) -> list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any]]:
    """Get observables for a variable name (may be nested path).

    Returns a list of observables to subscribe to. This includes Observable,
    ObservableList, ObservableDict, and ObservableSet since they all have on_change methods.
    """
    from qtpie.variable import Variable

    result: list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any]] = []

    # Try to resolve as binding source
    source = resolve_binding_source(widget, name)
    if source is not None:
        if isinstance(source, Variable):
            obs = source.observable
            if isinstance(obs, Observable):
                result.append(obs)
            elif isinstance(obs, ObservableList):
                result.append(obs)
            elif isinstance(obs, ObservableDict):
                result.append(obs)
            elif isinstance(obs, ObservableSet):
                result.append(obs)
            # else: ObservableProxy - doesn't directly fit Observable[Any], skip
        elif isinstance(source, Observable):
            result.append(source)
        elif isinstance(source, ObservableList):
            result.append(source)
        elif isinstance(source, ObservableDict):
            result.append(source)
        elif isinstance(source, ObservableSet):
            result.append(source)
        # else: ObservableProxy - for nested paths, skip for now

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
    widget: Widget[Any] | Window[Any],
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
      - {#app} - the QApplication instance (for accessing App class properties)

    Args:
        widget: The Widget or Window instance to resolve paths from.
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
    uses_app = any("#app" in f.expression for f in fields)

    # Get ROOT names for building eval context
    root_names = _get_root_names(var_names)

    # Collect all observables to subscribe to
    # Include ObservableList, ObservableDict, and ObservableSet since they also have on_change
    all_observables: list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any]] = []

    for name in var_names:
        obs_list = _get_observables_for_name(widget, name)
        all_observables.extend(obs_list)

    # If we have a variable, subscribe to it too
    if variable is not None:
        if isinstance(variable, Variable):
            obs = variable.observable
            if isinstance(obs, Observable):
                all_observables.append(obs)
            elif isinstance(obs, ObservableList):
                all_observables.append(obs)
            elif isinstance(obs, ObservableDict):
                all_observables.append(obs)
            elif isinstance(obs, ObservableSet):
                all_observables.append(obs)
        elif isinstance(variable, Observable):
            all_observables.append(variable)
        elif isinstance(variable, ObservableList):
            all_observables.append(variable)
        elif isinstance(variable, ObservableDict):
            all_observables.append(variable)
        elif isinstance(variable, ObservableSet):
            all_observables.append(variable)

    # Build the compute function
    def compute() -> str:
        # Build context with current values using root names
        context: dict[str, Any] = {}

        # Add #widget as 'widget_ref' in context if used
        if uses_widget:
            context["widget_ref"] = widget

        # Add #app - find the QApplication instance
        if uses_app:
            from qtpy.QtWidgets import QApplication

            context["app_ref"] = QApplication.instance()

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
        # Resolution order: exact match -> record -> underscore fallback
        for root_name in root_names:
            # 1. Try exact match first (e.g., 'name' -> widget.name)
            if hasattr(widget, root_name):
                raw_attr: Any = getattr(widget, root_name)
                if isinstance(raw_attr, Variable):
                    context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                else:
                    context[root_name] = raw_attr
                continue

            # 2. Try record fields if Widget[T]
            if hasattr(widget, "_qtpie_config"):
                config = widget._qtpie_config  # pyright: ignore[reportPrivateUsage]
                if config.record_type is not None:
                    try:
                        record = widget.record
                        if hasattr(record.observable, root_name):
                            obs = getattr(record.observable, root_name)
                            if isinstance(obs, Observable):
                                context[root_name] = obs.get()
                                continue
                    except (TypeError, AttributeError):
                        pass

            # 3. Underscore fallback (e.g., 'name' -> widget._name)
            underscore_name = f"_{root_name}"
            if hasattr(widget, underscore_name):
                raw_attr = getattr(widget, underscore_name)
                if isinstance(raw_attr, Variable):
                    context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                else:
                    context[root_name] = raw_attr

        # Process each field and build the result
        result_parts: list[str] = []

        for literal_text, field in _parse_format_template(template):
            result_parts.append(literal_text)

            if field is not None:
                # Handle special # placeholders - replace all occurrences
                eval_expr = field.expression
                eval_expr = eval_expr.replace("#self", "self")
                eval_expr = eval_expr.replace("#var", "var")
                eval_expr = eval_expr.replace("#widget", "widget_ref")
                eval_expr = eval_expr.replace("#window", "widget_ref")
                eval_expr = eval_expr.replace("#app", "app_ref")

                # Evaluate the expression
                try:
                    value: Any = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                    # Unwrap Observable/ObservableProxy results (from nested property access)
                    if isinstance(value, Observable):
                        value = value.get()  # pyright: ignore[reportUnknownVariableType]
                    elif isinstance(value, ObservableProxy):
                        value = value.unwrap()  # pyright: ignore[reportUnknownVariableType]
                    # If value is callable (method without parens), call it
                    if callable(value) and not isinstance(value, type):  # pyright: ignore[reportUnknownArgumentType]
                        value = value()
                except Exception:
                    value = f"<error: {field.expression}>"

                # Apply format spec if present
                if field.format_spec:
                    try:
                        value = format(value, field.format_spec)  # pyright: ignore[reportUnknownArgumentType]
                    except Exception:
                        value = str(value)  # pyright: ignore[reportUnknownArgumentType]
                else:
                    value = str(value)  # pyright: ignore[reportUnknownArgumentType]

                result_parts.append(value)

        return "".join(result_parts)

    # Set initial value
    setter(compute())

    # Subscribe to ALL observables - when any changes, recompute
    # Use *args because Observable passes value, but ObservableList/Dict pass nothing
    def on_any_change(*_: Any) -> None:
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
    elif isinstance(source, ObservableList):
        return source.to_list()
    elif isinstance(source, ObservableDict):
        return source.to_dict()
    elif isinstance(source, ObservableSet):
        return source.to_set()
    else:
        # ObservableProxy
        return source.unwrap()


def get_static_value(widget: Widget[Any], path: str) -> Any:
    """Try to get a static (non-reactive) attribute value.

    Handles paths like 'title' or nested paths like 'config.name'.
    Resolution order: exact match first, then underscore fallback.
    """
    lookup_path = path.lstrip("_")
    parts = lookup_path.split(".")

    current: Any = widget
    for part in parts:
        # Try exact match first, then underscore fallback
        if hasattr(current, part):
            current = getattr(current, part)
        elif hasattr(current, f"_{part}"):
            current = getattr(current, f"_{part}")
        else:
            return None
    return current


def create_item_formatter(template: str) -> Callable[[Any], str]:
    """Create a function that formats an item using a template string.

    Supports the full QtPie expression language:
    - Simple fields: {name}, {age}
    - Method calls: {name.upper()}, {name.strip()}
    - Function calls: {len(name)}, {str(age)}
    - Math: {age * 2}, {price + tax}
    - Format specs: {price:.2f}

    The item is available as both direct attribute access and via #self:
        "{name}" - access item.name
        "{#self.name}" - same thing
        "{#self}" - the item itself (useful for primitives)

    Args:
        template: Format string like "{name} ({age})" or "{name.upper()}"

    Returns:
        A callable that takes an item and returns the formatted string.

    Example:
        formatter = create_item_formatter("{name} - {age} years")
        result = formatter(Dog("Fido", 3))  # "Fido - 3 years"
    """
    # Parse the template once
    parsed = _parse_format_template(template)
    fields = _parse_format_fields(template)

    # Get all variable names used in the template (excluding #self)
    var_names = _get_variable_names(fields)

    # Check for #self usage
    uses_self = any("#self" in f.expression for f in fields)

    def format_item(item: Any) -> str:
        """Format a single item using the template."""
        # Build context with item attributes
        context: dict[str, Any] = {}

        # Add #self reference
        if uses_self:
            context["self"] = item

        # Add item attributes to context
        for name in var_names:
            root = name.split(".")[0]
            if hasattr(item, root):
                context[root] = getattr(item, root)

        # Process each field and build the result
        result_parts: list[str] = []

        for literal_text, field in parsed:
            result_parts.append(literal_text)

            if field is not None:
                # Handle #self placeholder
                eval_expr = field.expression
                eval_expr = eval_expr.replace("#self", "self")

                # Evaluate the expression
                try:
                    value: Any = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                    # Unwrap Observable results if any
                    if isinstance(value, Observable):
                        value = value.get()  # pyright: ignore[reportUnknownVariableType]
                    # If value is callable (method without parens), call it
                    if callable(value) and not isinstance(value, type):  # pyright: ignore[reportUnknownArgumentType]
                        value = value()
                except Exception:
                    value = f"<error: {field.expression}>"

                # Apply format spec if present
                if field.format_spec:
                    try:
                        value = format(value, field.format_spec)  # pyright: ignore[reportUnknownArgumentType]
                    except Exception:
                        value = str(value)  # pyright: ignore[reportUnknownArgumentType]
                else:
                    value = str(value)  # pyright: ignore[reportUnknownArgumentType]

                result_parts.append(value)

        return "".join(result_parts)

    return format_item
