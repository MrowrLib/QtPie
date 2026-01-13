"""Format string binding support with Python expression evaluation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any, cast

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


def _eval_with_optional_chaining(expr: str, context: dict[str, Any]) -> Any:
    """Evaluate an expression with ?. optional chaining support.

    Converts expressions like 'workspace?.name' to safe navigation that returns
    None if any intermediate value is None.

    Example: 'workspace?.name' with workspace=None returns None instead of raising.
    Example: 'workspace?.owner?.name' returns None if workspace or owner is None.
    """
    # Parse the expression to find ?. chains
    # Strategy: for simple dotted paths with ?., manually traverse
    # For complex expressions, we need a different approach

    # Check if this is a simple dotted path (no operators, function calls, etc.)
    # Simple: workspace?.name, config?.theme?.name
    # Complex: workspace?.name + other, func(workspace?.name)
    normalized = expr.replace("?.", ".")
    if _is_simple_name(normalized):
        # Simple dotted path - traverse manually with None checks
        return _traverse_optional_path(expr, context)

    # For complex expressions, convert ?. to a safe pattern
    # This is a simple approach: split on ?. and build getattr chain
    # More sophisticated parsing would require a full expression parser
    # For now, just try eval and let it fail gracefully
    try:
        # Replace ?. with . and hope for the best (caller catches exceptions)
        safe_expr = expr.replace("?.", ".")
        return eval(safe_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
    except (AttributeError, TypeError):
        return None


def _traverse_optional_path(expr: str, context: dict[str, Any]) -> Any:
    """Traverse a dotted path with ?. optional chaining.

    Returns None if any segment is None or missing.
    """
    # Parse segments: "workspace?.name" -> [("workspace", True), ("name", False)]
    segments: list[tuple[str, bool]] = []
    remaining = expr
    while remaining:
        optional_idx = remaining.find("?.")
        regular_idx = remaining.find(".")

        if optional_idx == -1 and regular_idx == -1:
            # Last segment
            segments.append((remaining, False))
            break
        elif optional_idx != -1 and (regular_idx == -1 or optional_idx < regular_idx):
            # Optional chain comes first
            segments.append((remaining[:optional_idx], True))
            remaining = remaining[optional_idx + 2 :]  # Skip ?.
        else:
            # Regular chain comes first
            segments.append((remaining[:regular_idx], False))
            remaining = remaining[regular_idx + 1 :]  # Skip .

    if not segments:
        return None

    # Get the root from context
    root_name, is_optional = segments[0]
    if root_name not in context:
        return None
    current: Any = context[root_name]

    # If root is optional and None, return None
    if is_optional and current is None:
        return None

    # Traverse remaining segments
    for attr_name, is_opt in segments[1:]:
        if current is None:
            return None
        if not hasattr(current, attr_name):
            if is_opt:
                return None
            # Required attribute missing - let caller handle
            raise AttributeError(f"'{type(current).__name__}' has no attribute '{attr_name}'")
        current = getattr(current, attr_name)
        if is_opt and current is None:
            return None

    return current


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


def _get_observables_for_name(widget: Widget[Any] | Window[Any], name: str) -> list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]]:
    """Get observables for a variable name (may be nested path).

    Returns a list of observables to subscribe to. This includes Observable,
    ObservableList, ObservableDict, ObservableSet, and ObservableProxy since they all have on_change methods.

    Also searches parent widget hierarchy for Variables not found on the immediate widget.
    """
    from qtpie.variable import (
        Variable,
        _try_get_variable,  # pyright: ignore[reportPrivateUsage]
    )

    # All observable types have on_change, so we can use a union
    result: list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]] = []

    def add_source(source: BindingSource) -> None:
        if isinstance(source, Variable):
            result.append(source.observable)
        else:
            result.append(source)

    # Try to resolve as binding source (full path) on current widget
    source = resolve_binding_source(widget, name)
    if source is not None:
        add_source(source)

    # Get root name for parent hierarchy lookup
    normalized = name.replace("?.", ".")
    root_name = normalized.split(".")[0]

    # For nested paths like "workspace.name", also try to subscribe to the ROOT Variable
    # This is critical for bare Variables resolved from hierarchy (descriptors)
    if "." in normalized:
        # Try root name directly on widget (handles descriptors like bare Variables)
        root_attr: Any = getattr(widget, root_name, None)
        if root_attr is not None and isinstance(root_attr, Variable):
            add_source(cast(BindingSource, root_attr))

    # If we didn't find anything, search parent hierarchy
    if not result:
        from qtpy.QtWidgets import QApplication

        # Also try underscore variants
        lookup_name = root_name.lstrip("_")
        underscore_name = f"_{lookup_name}"

        current: Any = widget
        while True:
            if not hasattr(current, "parent") or not callable(current.parent):
                break
            parent: Any = current.parent()
            if parent is None:
                break

            # Try all name variants
            for attr_name in [root_name, lookup_name, underscore_name]:
                found = _try_get_variable(parent, attr_name)
                if found is not None:
                    add_source(cast(BindingSource, found))
                    break
            if result:
                break

            current = parent

        # Fallback: check QApplication.instance()
        if not result:
            app = QApplication.instance()
            if app is not None:
                for attr_name in [root_name, lookup_name, underscore_name]:
                    found = _try_get_variable(app, attr_name)
                    if found is not None:
                        add_source(cast(BindingSource, found))
                        break

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
    widget: Widget[Any] | Window[Any] | Any,  # Also accepts AppBase
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
    # Include ObservableList, ObservableDict, ObservableSet, and ObservableProxy since they all have on_change
    all_observables: list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]] = []

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
        # Resolution order: exact match -> record -> underscore fallback -> parent hierarchy
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
                continue

            # 4. Search parent widget hierarchy
            from qtpy.QtWidgets import QApplication as QApp

            from qtpie.variable import _try_get_variable  # pyright: ignore[reportPrivateUsage]

            lookup_name = root_name.lstrip("_")
            underscore_variant = f"_{lookup_name}"
            found_in_parent = False

            current: Any = widget
            while not found_in_parent:
                if not hasattr(current, "parent") or not callable(current.parent):
                    break
                parent_widget: Any = current.parent()
                if parent_widget is None:
                    break

                for attr_name in [root_name, lookup_name, underscore_variant]:
                    found_var = _try_get_variable(parent_widget, attr_name)
                    if found_var is not None:
                        context[root_name] = found_var.value  # pyright: ignore[reportUnknownMemberType]
                        found_in_parent = True
                        break

                current = parent_widget

            # 5. Fallback: check QApplication.instance()
            if not found_in_parent and root_name not in context:
                app_instance = QApp.instance()
                if app_instance is not None:
                    for attr_name in [root_name, lookup_name, underscore_variant]:
                        found_var = _try_get_variable(app_instance, attr_name)
                        if found_var is not None:
                            context[root_name] = found_var.value  # pyright: ignore[reportUnknownMemberType]
                            break

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
                    # Handle ?. optional chaining by converting to safe navigation
                    if "?." in eval_expr:
                        value = _eval_with_optional_chaining(eval_expr, context)
                    else:
                        value = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
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

    # Subscribe to ALL observables - when any changes, recompute
    # Use *args because Observable passes value, but ObservableList/Dict pass nothing
    def on_any_change(*_: Any) -> None:
        setter(compute())

    # Track subscribed observables to avoid duplicates
    subscribed: set[int] = set()

    def subscribe_to(obs: Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]) -> None:
        obs_id = id(obs)
        if obs_id not in subscribed:
            subscribed.add(obs_id)
            obs.on_change(on_any_change)

    for obs in all_observables:
        subscribe_to(obs)

    # Set initial value
    setter(compute())

    # Deferred subscription: check for parent Variables after parenting is complete
    # This handles bindings that reference Variables in parent widgets but the widget
    # wasn't parented yet when create_format_binding was called.
    #
    # The challenge: Qt parenting can be multi-level (widget -> intermediate -> actual parent).
    # The child widget only gets ParentChange when it's parented to the intermediate,
    # NOT when the intermediate is parented to the actual parent with the Variables.
    #
    # Solution: Use both immediate event watching AND a deferred timer check.
    from qtpy.QtCore import QObject, QTimer

    def try_subscribe_from_parents() -> bool:
        """Try to find and subscribe to parent Variables. Returns True if any found."""
        found_any = False
        for name in var_names:
            obs_list = _get_observables_for_name(widget, name)  # type: ignore[arg-type]
            for obs in obs_list:
                obs_id = id(obs)
                if obs_id not in subscribed:
                    subscribe_to(obs)
                    found_any = True
        return found_any

    def on_deferred_check() -> None:
        """Deferred check for parent Variables after event loop processes."""
        if try_subscribe_from_parents():
            setter(compute())

    # Only do deferred subscription if we have variable names to look up and widget is a QObject
    if var_names and isinstance(widget, QObject):
        # Check if already parented to something with the Variables we need
        if not try_subscribe_from_parents():
            # Didn't find parent Variables yet - schedule a deferred check
            # This runs after the current call stack completes, when parenting should be done
            QTimer.singleShot(0, on_deferred_check)
        else:
            # Found parent Variables, recompute
            setter(compute())


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
