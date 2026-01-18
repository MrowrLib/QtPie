"""Expression binding utilities shared across Widget, Window, App, Menu."""

import re
from collections.abc import Callable
from typing import Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy


def _try_get_variable_from_obj(obj: Any, var_name: str) -> Any | None:
    """Try to get a Variable from an object by name (with underscore variants)."""
    from qtpie.variable import Variable

    for attr_name in [var_name, f"_{var_name}"]:
        if hasattr(obj, attr_name):
            raw_attr: Any = getattr(obj, attr_name)
            if isinstance(raw_attr, Variable):
                return raw_attr  # pyright: ignore[reportUnknownVariableType]
    return None


def find_variable_in_hierarchy(context: Any, name: str) -> Any | None:
    """Find a Variable by name in the widget hierarchy (without unwrapping value).

    Searches in this order:
    1. The context object itself (with and without underscore prefix)
    2. Logical parent chain (set during widget creation, before Qt parenting)
    3. Parent widget hierarchy (walking up parent() chain)
    4. QApplication.instance() for app-level Variables

    Args:
        context: The context object (Widget, Window, App, or Menu instance).
        name: The variable name to resolve (e.g., "count" or "_count").

    Returns:
        The Variable object if found, None otherwise.
    """
    from qtpie.state import QtPieState

    # Try on context itself
    found = _try_get_variable_from_obj(context, name)
    if found is not None:
        return found

    current: Any = context

    # Walk up the logical parent chain (set during widget creation, before Qt parenting)
    logical_current = context
    while True:
        lp_state = getattr(logical_current, "_qtpie", None)
        if not isinstance(lp_state, QtPieState) or lp_state._logical_parent is None:  # pyright: ignore[reportPrivateUsage]
            break
        logical_parent = lp_state._logical_parent  # pyright: ignore[reportPrivateUsage]
        found = _try_get_variable_from_obj(logical_parent, name)
        if found is not None:
            return found
        # Move up the logical parent chain
        logical_current = logical_parent
        # Also update current for Qt parent traversal starting point
        current = logical_parent

    # Search Qt parent hierarchy
    if hasattr(current, "parent") and callable(current.parent):
        from qtpy.QtWidgets import QApplication

        while True:
            parent_obj: Any = current.parent() if hasattr(current, "parent") and callable(current.parent) else None
            if parent_obj is None:
                break

            found = _try_get_variable_from_obj(parent_obj, name)
            if found is not None:
                return found

            current = parent_obj

        # Check QApplication.instance() for app-level Variables
        app_instance = QApplication.instance()
        if app_instance is not None:
            found = _try_get_variable_from_obj(app_instance, name)
            if found is not None:
                return found

    return None


def resolve_var(context: Any, name: str) -> Any:
    """Resolve a variable by name from the binding context.

    Searches in this order:
    1. The context object itself (with and without underscore prefix)
    2. Logical parent chain (set during widget creation, before Qt parenting)
    3. Parent widget hierarchy (walking up parent() chain)
    4. QApplication.instance() for app-level Variables

    Args:
        context: The context object (Widget, Window, App, or Menu instance).
        name: The variable name to resolve (e.g., "count" or "_count").

    Returns:
        The resolved value (unwrapped from Variable if applicable).

    Raises:
        AttributeError: If variable not found in context or parent hierarchy.

    Example:
        # In a widget method:
        count = self.var("count")  # Gets current value of _count Variable
        item = self.var("selected_item")  # May resolve from parent widget
    """
    from qtpie.state import QtPieState
    from qtpie.variable import Variable

    # Try on context itself (with underscore variants)
    for attr_name in [name, f"_{name}"]:
        if hasattr(context, attr_name):
            raw_attr: Any = getattr(context, attr_name)
            if isinstance(raw_attr, Variable):
                return raw_attr.value  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            return raw_attr  # pyright: ignore[reportUnknownVariableType]

    current: Any = context

    # Walk up the logical parent chain (set during widget creation, before Qt parenting)
    logical_current = context
    while True:
        lp_state = getattr(logical_current, "_qtpie", None)
        if not isinstance(lp_state, QtPieState) or lp_state._logical_parent is None:  # pyright: ignore[reportPrivateUsage]
            break
        logical_parent = lp_state._logical_parent  # pyright: ignore[reportPrivateUsage]
        found_var = _try_get_variable_from_obj(logical_parent, name)
        if found_var is not None:
            return found_var.value  # pyright: ignore[reportUnknownMemberType]
        # Move up the logical parent chain
        logical_current = logical_parent
        # Also update current for Qt parent traversal starting point
        current = logical_parent

    # Search Qt parent hierarchy
    if hasattr(current, "parent") and callable(current.parent):
        from qtpy.QtWidgets import QApplication

        while True:
            parent_obj: Any = current.parent() if hasattr(current, "parent") and callable(current.parent) else None
            if parent_obj is None:
                break

            found_var = _try_get_variable_from_obj(parent_obj, name)
            if found_var is not None:
                return found_var.value  # pyright: ignore[reportUnknownMemberType]

            current = parent_obj

        # Check QApplication.instance() for app-level Variables
        app_instance = QApplication.instance()
        if app_instance is not None:
            found_var = _try_get_variable_from_obj(app_instance, name)
            if found_var is not None:
                return found_var.value  # pyright: ignore[reportUnknownMemberType]

    raise AttributeError(f"Variable '{name}' not found on {type(context).__name__} or in parent hierarchy")


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

    # Track which variables we found on the context vs need to search parents for
    found_on_context: set[str] = set()

    # For Widget[T], get record proxy early to subscribe to record field changes
    # This is needed because widget fields might shadow record fields (e.g., body_type: QComboBox
    # shadows record.body_type), but we want expressions to use record field values
    record_proxy_for_subscriptions: ObservableProxy[Any] | None = None
    if hasattr(context, "_qtpie_config"):
        ctx_config: Any = context._qtpie_config
        if hasattr(ctx_config, "record_type") and ctx_config.record_type is not None:
            if hasattr(context, "record") and hasattr(context.record, "observable"):
                record_proxy_for_subscriptions = context.record.observable

    for var_name in var_names:
        source = resolve_binding_source(context, var_name)  # type: ignore[arg-type]
        if source is not None:
            found_on_context.add(var_name)
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
                    if isinstance(raw_attr, Variable):
                        found_on_context.add(var_name)
                        obs = raw_attr.observable  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                        if isinstance(obs, Observable):
                            observables.append(cast(Observable[Any], obs))
                        elif isinstance(obs, (ObservableList, ObservableDict, ObservableProxy)):
                            reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obs))
                        break
                    elif isinstance(raw_attr, Observable):
                        found_on_context.add(var_name)
                        observables.append(cast(Observable[Any], raw_attr))
                        break
                    elif isinstance(raw_attr, (ObservableList, ObservableDict, ObservableProxy)):
                        found_on_context.add(var_name)
                        reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], raw_attr))
                        break

    # For Widget[T], also subscribe to record proxy changes. This handles two cases:
    # 1. When the record target is initially None and gets set later (timing issue)
    # 2. When record fields change that might be shadowed by widget fields
    if record_proxy_for_subscriptions is not None:
        # Always subscribe to the proxy itself - this fires when target is set or any field changes
        if record_proxy_for_subscriptions not in reactive_collections:
            reactive_collections.append(record_proxy_for_subscriptions)

        # Also subscribe to specific field Observables if target is already set
        target = object.__getattribute__(record_proxy_for_subscriptions, "_target")
        if target is not None:
            for var_name in var_names:
                if hasattr(target, var_name):
                    # Get the Observable/ObservableProxy for this record field
                    try:
                        field_obs = record_proxy_for_subscriptions.observable_for_path(var_name)
                        # Subscribe to the record field Observable
                        if isinstance(field_obs, Observable):
                            if field_obs not in observables:
                                observables.append(field_obs)
                        else:
                            # ObservableList, ObservableDict, or ObservableProxy
                            if field_obs not in reactive_collections:
                                reactive_collections.append(field_obs)
                    except AttributeError:
                        pass  # Field doesn't exist on record, skip

    # Search parent widget hierarchy for variables not found on context
    # This allows expressions like isinstance(collection_item, Request) where
    # collection_item is on a parent widget
    vars_needing_parent_lookup = var_names - found_on_context
    parent_var_sources: dict[str, Variable[Any]] = {}

    if vars_needing_parent_lookup and hasattr(context, "parent") and callable(context.parent):
        from qtpy.QtWidgets import QApplication

        current: Any = context
        while vars_needing_parent_lookup:
            parent_obj: Any = current.parent() if hasattr(current, "parent") and callable(current.parent) else None
            if parent_obj is None:
                break

            for var_name in list(vars_needing_parent_lookup):
                found_var = _try_get_variable_from_obj(parent_obj, var_name)
                if found_var is not None:
                    parent_var_sources[var_name] = found_var
                    vars_needing_parent_lookup.discard(var_name)
                    # Subscribe to the parent's Variable
                    obs = found_var.observable
                    if isinstance(obs, Observable):
                        observables.append(cast(Observable[Any], obs))
                    elif isinstance(obs, (ObservableList, ObservableDict, ObservableProxy)):
                        reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obs))

            current = parent_obj

        # Also check QApplication.instance() for app-level Variables
        if vars_needing_parent_lookup:
            app_instance = QApplication.instance()
            if app_instance is not None:
                for var_name in list(vars_needing_parent_lookup):
                    found_var = _try_get_variable_from_obj(app_instance, var_name)
                    if found_var is not None:
                        parent_var_sources[var_name] = found_var
                        vars_needing_parent_lookup.discard(var_name)
                        obs = found_var.observable
                        if isinstance(obs, Observable):
                            observables.append(cast(Observable[Any], obs))
                        elif isinstance(obs, (ObservableList, ObservableDict, ObservableProxy)):
                            reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obs))

    # Also check for nested Observable paths like "view_model.is_dirty" or "record.is_valid"
    # or "auth?.type" (with optional chaining)
    # Find patterns like "name.attr", "name?.attr", or "name.attr.method()" in the expression
    nested_patterns = re.findall(r"\b(\w+(?:[?]?\.[\w]+)+)(?:\s*\()?", expr)
    for path in nested_patterns:
        # Normalize ?. to . for attribute lookup
        normalized_path = path.replace("?.", ".")
        # Try to evaluate the path to find Observables
        # Stop at paths that end with method calls like ".get()"
        parts = normalized_path.split(".")
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

        # For Widget[T], also try to subscribe to nested record paths like "auth.type"
        # This allows expressions like "{auth?.type == AuthType.BASIC}" to work
        if record_proxy_for_subscriptions is not None:
            target = object.__getattribute__(record_proxy_for_subscriptions, "_target")
            if target is not None:
                try:
                    # Try to resolve the full path on the record proxy
                    field_obs = record_proxy_for_subscriptions.observable_for_path(normalized_path)
                    if isinstance(field_obs, Observable):
                        if field_obs not in observables:
                            observables.append(field_obs)
                    elif field_obs not in reactive_collections:
                        # ObservableList, ObservableDict, or ObservableProxy
                        reactive_collections.append(field_obs)
                except (AttributeError, ValueError):
                    pass  # Path doesn't exist on record or intermediate is None

    # Get module globals for class lookups (for isinstance checks)
    # This allows expressions like isinstance(item, Request) to work
    module_globals: dict[str, Any] = {}
    context_class = type(context)  # pyright: ignore[reportUnknownVariableType]
    if hasattr(context_class, "__module__"):  # pyright: ignore[reportUnknownArgumentType]
        import sys

        module = sys.modules.get(context_class.__module__)
        if module is not None:
            module_globals = vars(module)

    def compute() -> Any:
        # Re-resolve record proxy each time - bind="record" may have changed it after setup
        record_proxy: ObservableProxy[Any] | None = None
        if hasattr(context, "_qtpie_config"):
            ctx_config: Any = context._qtpie_config
            if hasattr(ctx_config, "record_type") and ctx_config.record_type is not None:
                if hasattr(context, "record") and hasattr(context.record, "observable"):
                    record_proxy = context.record.observable

        # Build context with current values
        eval_context: dict[str, Any] = {}

        for var_name in var_names:
            # First check if we found this in parent hierarchy
            if var_name in parent_var_sources:
                eval_context[var_name] = parent_var_sources[var_name].value  # pyright: ignore[reportUnknownMemberType]
                continue

            # For Widget[T], check if this is a record field first
            # This allows expressions like "{body_type in [...]}" to reference record.body_type
            # even when there's a widget field with the same name
            if record_proxy is not None:
                target: Any = object.__getattribute__(record_proxy, "_target")
                if target is not None and hasattr(target, var_name):
                    # Get the actual value from the record (not the proxy)
                    field_value = getattr(target, var_name)
                    eval_context[var_name] = field_value
                    continue

            # Try with underscore prefix first, then without on the context
            for attr_name in [f"_{var_name}", var_name]:
                if hasattr(context, attr_name):
                    raw_attr: Any = getattr(context, attr_name)
                    if isinstance(raw_attr, Variable):
                        eval_context[var_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                    elif isinstance(raw_attr, ObservableProxy):
                        # Unwrap ObservableProxy to get the actual value
                        eval_context[var_name] = raw_attr.unwrap()
                    else:
                        eval_context[var_name] = raw_attr
                    break
            else:
                # Not found on context - check module globals (for classes like Request)
                if var_name in module_globals:
                    eval_context[var_name] = module_globals[var_name]

        # Evaluate the expression
        try:
            # Handle ?. optional chaining by converting to safe navigation
            if "?." in expr:
                from qtpie.bindings.format_binding import (
                    _eval_with_optional_chaining,  # pyright: ignore[reportPrivateUsage]
                )

                return _eval_with_optional_chaining(expr, eval_context)
            value = eval(expr, {"__builtins__": __builtins__}, eval_context)  # noqa: S307
            return value
        except Exception:
            return None

    # Subscribe to ALL reactive objects - when any changes, recompute
    # Observable.on_change takes Callable[[T], None]
    def on_observable_change(_: Any) -> None:
        setter(compute())

    # ObservableList/Dict/Proxy.on_change takes Callable[[], None]
    def on_collection_change() -> None:
        setter(compute())

    # Track subscribed observables to avoid duplicates
    subscribed: set[int] = set()

    def subscribe_to_observable(obs: Observable[Any]) -> None:
        obs_id = id(obs)
        if obs_id not in subscribed:
            subscribed.add(obs_id)
            obs.on_change(on_observable_change)

    def subscribe_to_collection(coll: ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any]) -> None:
        coll_id = id(coll)
        if coll_id not in subscribed:
            subscribed.add(coll_id)
            coll.on_change(on_collection_change)

    for obs in observables:
        subscribe_to_observable(obs)

    for coll in reactive_collections:
        subscribe_to_collection(coll)

    # Set initial value
    setter(compute())

    # Deferred record subscription: for Widget[T], the record may not be bound yet at setup time
    # (e.g., child widget with bind="record" from parent). Schedule a check after bindings complete.
    if record_proxy_for_subscriptions is not None and hasattr(context, "parent") and callable(context.parent):
        from qtpy.QtCore import QObject, QTimer

        def try_deferred_record_subscription() -> None:
            """Check if record proxy changed after bindings and subscribe to the new one."""
            # Re-resolve the record proxy
            new_proxy: ObservableProxy[Any] | None = None
            if hasattr(context, "_qtpie_config"):
                ctx_config: Any = context._qtpie_config
                if hasattr(ctx_config, "record_type") and ctx_config.record_type is not None:
                    if hasattr(context, "record") and hasattr(context.record, "observable"):
                        new_proxy = context.record.observable

            # If it's a different proxy than we subscribed to, subscribe to the new one
            if new_proxy is not None and id(new_proxy) != id(record_proxy_for_subscriptions):
                # Subscribe to the new proxy
                subscribe_to_collection(new_proxy)

                # Also subscribe to specific field Observables
                target = object.__getattribute__(new_proxy, "_target")
                if target is not None:
                    for var_name in var_names:
                        if hasattr(target, var_name):
                            try:
                                field_obs = new_proxy.observable_for_path(var_name)
                                if isinstance(field_obs, Observable):
                                    subscribe_to_observable(field_obs)
                                else:
                                    subscribe_to_collection(field_obs)
                            except AttributeError:
                                pass

                # Recompute with new data
                setter(compute())

        # Schedule check after current event loop completes
        if isinstance(context, QObject):
            QTimer.singleShot(0, try_deferred_record_subscription)

    # Deferred parent lookup: if we still have unresolved variables, try again after parenting
    # This handles cases where the variable is on a parent widget that isn't connected yet
    if vars_needing_parent_lookup and hasattr(context, "parent") and callable(context.parent):
        from qtpy.QtCore import QObject, QTimer

        def try_deferred_parent_lookup() -> bool:
            """Try to find and subscribe to parent Variables. Returns True if any new ones found."""
            nonlocal vars_needing_parent_lookup
            found_any = False

            from qtpy.QtWidgets import QApplication

            current: Any = context
            while vars_needing_parent_lookup:
                parent_obj: Any = current.parent() if hasattr(current, "parent") and callable(current.parent) else None
                if parent_obj is None:
                    break

                for var_name in list(vars_needing_parent_lookup):
                    found_var = _try_get_variable_from_obj(parent_obj, var_name)
                    if found_var is not None:
                        parent_var_sources[var_name] = found_var
                        vars_needing_parent_lookup.discard(var_name)
                        found_any = True
                        # Subscribe to the parent's Variable
                        obs = found_var.observable  # pyright: ignore[reportUnknownMemberType]
                        if isinstance(obs, Observable):
                            subscribe_to_observable(cast(Observable[Any], obs))
                        elif isinstance(obs, (ObservableList, ObservableDict, ObservableProxy)):
                            subscribe_to_collection(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obs))

                current = parent_obj

            # Also check QApplication.instance()
            if vars_needing_parent_lookup:
                app_instance = QApplication.instance()
                if app_instance is not None:
                    for var_name in list(vars_needing_parent_lookup):
                        found_var = _try_get_variable_from_obj(app_instance, var_name)
                        if found_var is not None:
                            parent_var_sources[var_name] = found_var
                            vars_needing_parent_lookup.discard(var_name)
                            found_any = True
                            obs = found_var.observable  # pyright: ignore[reportUnknownMemberType]
                            if isinstance(obs, Observable):
                                subscribe_to_observable(cast(Observable[Any], obs))
                            elif isinstance(obs, (ObservableList, ObservableDict, ObservableProxy)):
                                subscribe_to_collection(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obs))

            return found_any

        def on_deferred_check() -> None:
            """Deferred check for parent Variables after event loop processes."""
            if try_deferred_parent_lookup():
                setter(compute())

        # Schedule deferred check after current call stack completes
        if isinstance(context, QObject):
            QTimer.singleShot(0, on_deferred_check)
