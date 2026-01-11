"""Expression binding utilities shared across Widget, Window, App, Menu."""

import re
from collections.abc import Callable
from typing import Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy


def create_expression_binding(
    context: Any,
    expression: str,
    setter: Callable[[Any], None],
) -> None:
    """Create a binding for an expression like "{_count > 0}".

    Unlike format bindings which return strings, this returns the raw evaluated value.
    This is used for property bindings like visible= and enabled= that need boolean results.

    Args:
        context: The context object (Widget, Window, App, or Menu instance).
        expression: The expression string like "{_count > 0}".
        setter: Function to call with the computed value.
    """
    from qtpie.bindings import resolve_binding_source
    from qtpie.bindings.format_binding import _BUILTINS, _extract_ast_names  # pyright: ignore[reportPrivateUsage]
    from qtpie.variable import Variable

    # Extract the expression from {expr}
    # Handle both "{expr}" and "expr" formats
    expr = expression.strip()
    if expr.startswith("{") and expr.endswith("}"):
        expr = expr[1:-1].strip()

    # Extract variable names from the expression
    ast_names = _extract_ast_names(expr)
    var_names = ast_names - _BUILTINS

    # Collect all reactive objects to subscribe to
    # Observable has on_change(callback: Callable[[T], None])
    # ObservableList/Dict/Proxy have on_change(callback: Callable[[], None])
    observables: list[Observable[Any]] = []
    reactive_collections: list[ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any]] = []

    for var_name in var_names:
        source = resolve_binding_source(context, var_name)  # type: ignore[arg-type]
        if source is not None:
            if isinstance(source, Variable):
                obs: Any = source.observable
                if isinstance(obs, Observable):
                    observables.append(cast(Observable[Any], obs))
                elif isinstance(obs, (ObservableList, ObservableDict, ObservableProxy)):
                    reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obs))
            elif isinstance(source, Observable):
                observables.append(source)
            elif isinstance(source, (ObservableList, ObservableDict, ObservableProxy)):  # pyright: ignore[reportUnnecessaryIsInstance]
                reactive_collections.append(source)
        else:
            # Also check for reactive attributes directly on the context
            # (e.g., is_valid returns Observable[bool])
            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(context, attr_name):
                    raw_attr: Any = getattr(context, attr_name)
                    if isinstance(raw_attr, Observable):
                        observables.append(cast(Observable[Any], raw_attr))
                        break
                    elif isinstance(raw_attr, (ObservableList, ObservableDict, ObservableProxy)):
                        reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], raw_attr))
                        break

    # Also check for nested Observable paths like "view_model.is_dirty" or "record.is_valid"
    # Find patterns like "name.attr" or "name.attr.method()" in the expression
    nested_patterns = re.findall(r"\b(\w+(?:\.\w+)+)(?:\s*\()?", expr)
    for path in nested_patterns:
        # Try to evaluate the path to find Observables
        # Stop at paths that end with method calls like ".get()"
        parts = path.split(".")
        # Try progressively longer paths to find Observable
        obj: Any = context
        for part in parts:
            if not hasattr(obj, part):
                break
            obj = getattr(obj, part)
            if isinstance(obj, Observable):
                if obj not in observables:
                    observables.append(cast(Observable[Any], obj))
                break
            elif isinstance(obj, (ObservableList, ObservableDict, ObservableProxy)):
                if obj not in reactive_collections:
                    reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obj))
                break

    def compute() -> Any:
        # Build context with current values
        eval_context: dict[str, Any] = {}

        for var_name in var_names:
            # Try with underscore prefix first, then without
            for attr_name in [f"_{var_name}", var_name]:
                if hasattr(context, attr_name):
                    raw_attr: Any = getattr(context, attr_name)
                    if isinstance(raw_attr, Variable):
                        eval_context[var_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                    else:
                        eval_context[var_name] = raw_attr
                    break

        # Evaluate the expression
        try:
            value = eval(expr, {"__builtins__": __builtins__}, eval_context)  # noqa: S307
            return value
        except Exception:
            return None

    # Set initial value
    setter(compute())

    # Subscribe to ALL reactive objects - when any changes, recompute
    # Observable.on_change takes Callable[[T], None]
    def on_observable_change(_: Any) -> None:
        setter(compute())

    for obs in observables:
        obs.on_change(on_observable_change)

    # ObservableList/Dict/Proxy.on_change takes Callable[[], None]
    def on_collection_change() -> None:
        setter(compute())

    for coll in reactive_collections:
        coll.on_change(on_collection_change)
