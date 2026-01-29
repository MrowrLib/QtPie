"""Expression-based binding for model widgets.

Allows model widgets (QListView, QTreeView, QTableView, QComboBox) to bind to
expression results like `bind="{items[0]}"` for one-way reactive binding.
"""

# pyright: reportPrivateUsage=false

from collections.abc import Callable
from typing import Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet
from qtpy.QtWidgets import QWidget

from qtpie.new_field import NewField


def create_expression_model_binding(
    host: QWidget,
    widget_instance: QWidget,
    expression: str,
    field_info: NewField,
    *,
    is_table_view_fn: Callable[[QWidget], bool],
    is_tree_view_fn: Callable[[QWidget], bool],
    resolve_or_create_variable_fn: Callable[[QWidget, str, type | None], Any],
) -> bool:
    """Create expression-based binding for model widgets.

    Evaluates the expression, extracts the result, and creates a managed
    ObservableList that stays in sync with the expression result.

    Args:
        host: The Widget/Window instance
        widget_instance: The model widget (QListView, QComboBox, etc.)
        expression: The format expression e.g., "{items[0]}" or "{workspace?.items}"
        field_info: The NewField containing configuration
        is_table_view_fn: Function to check if widget is QTableView
        is_tree_view_fn: Function to check if widget is QTreeView
        resolve_or_create_variable_fn: Function to resolve/create Variables

    Returns:
        True if binding was created successfully, False otherwise.
    """
    from qtpie.bindings.format_binding import (
        _eval_with_optional_chaining,
        _get_observables_for_name,
        _get_root_names,
        _get_variable_names,
        _parse_format_fields,
    )
    from qtpie.bindings.model_binding import apply_model_binding
    from qtpie.variable import Variable

    # Parse the expression to extract field references
    fields = _parse_format_fields(expression)
    if not fields:
        return False

    # We need exactly ONE field for model binding - the collection source
    # (Multiple fields would be for display formatting, not data source)
    if len(fields) != 1:
        return False

    # Get all variable names referenced in the expression
    var_names = _get_variable_names(fields)
    root_names = _get_root_names(var_names)

    # Collect all observables to subscribe to for reactivity
    all_observables: list[Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]] = []

    for name in var_names:
        obs_list = _get_observables_for_name(host, name)  # type: ignore[arg-type]
        for obs in obs_list:
            all_observables.append(obs)

    # For Widget[T] record bindings, also subscribe to the record proxy
    # so we re-evaluate when the record changes (e.g., from None to a real object)
    config: Any = getattr(host, "_qtpie_config", None)
    if config is not None and getattr(config, "record_type", None) is not None:
        from qtpie.variable import RecordVariable

        record_var: Any = getattr(host, "record", None)
        if record_var is not None and isinstance(record_var, RecordVariable):
            all_observables.append(record_var.observable)  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]

    # Function to evaluate the expression and get the result
    def evaluate_expression() -> Any:
        """Evaluate the expression and return the result."""
        field = fields[0]
        expr = field.expression

        # Build context with current values
        context: dict[str, Any] = {}

        for root_name in root_names:
            # Try to get the value from the widget
            # 1. Try explicit QtPie fields by EXACT name
            config: Any = getattr(host, "_qtpie_config", None)
            if config is not None and hasattr(config, "fields") and root_name in config.fields:
                raw_attr: Any = getattr(host, root_name, None)
                if raw_attr is not None:
                    if isinstance(raw_attr, Variable):
                        context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                    else:
                        context[root_name] = raw_attr
                    continue

            # 2. Check if it's a Variable directly
            raw_attr = getattr(host, root_name, None)
            if raw_attr is not None and isinstance(raw_attr, Variable):
                context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                continue

            # 3. Try record fields if Widget[T]
            if config is not None and getattr(config, "record_type", None) is not None:
                try:
                    record: Any = getattr(host, "record", None)
                    if record is not None:
                        proxy: Any = getattr(record, "observable", None)
                        if proxy is not None:
                            target: Any = object.__getattribute__(proxy, "_target")
                            if target is not None and hasattr(target, root_name):
                                field_obs: Any = getattr(proxy, root_name)
                                if isinstance(field_obs, Observable):
                                    context[root_name] = field_obs.get()
                                    continue
                                elif isinstance(field_obs, ObservableProxy):
                                    context[root_name] = field_obs.unwrap()
                                    continue
                                elif isinstance(field_obs, ObservableDict):
                                    context[root_name] = field_obs.to_dict()
                                    continue
                                elif isinstance(field_obs, ObservableList):
                                    context[root_name] = field_obs.to_list()
                                    continue
                except (TypeError, AttributeError):
                    pass

            # 4. Underscore fallback
            underscore_name = f"_{root_name}"
            if hasattr(host, underscore_name):
                raw_attr = getattr(host, underscore_name)
                if isinstance(raw_attr, Variable):
                    context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                else:
                    context[root_name] = raw_attr
                continue

            # 5. Search parent widget hierarchy
            from qtpy.QtWidgets import QApplication

            from qtpie.variable import _try_get_variable  # pyright: ignore[reportPrivateUsage]

            lookup_name = root_name.lstrip("_")
            underscore_variant = f"_{lookup_name}"
            found_in_parent = False

            current: Any = host
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

            # 6. Fallback: check QApplication.instance()
            if not found_in_parent and root_name not in context:
                app_instance = QApplication.instance()
                if app_instance is not None:
                    for attr_name in [root_name, lookup_name, underscore_variant]:
                        found_var = _try_get_variable(app_instance, attr_name)
                        if found_var is not None:
                            context[root_name] = found_var.value  # pyright: ignore[reportUnknownMemberType]
                            break

        # Evaluate the expression
        try:
            result: Any
            if "?." in expr:
                result = _eval_with_optional_chaining(expr, context)
            else:
                result = eval(expr, {"__builtins__": __builtins__}, context)  # noqa: S307

            # Unwrap Observable and Variable results
            if isinstance(result, Variable):
                result = result.value  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]
            elif isinstance(result, Observable):
                result = result.get()  # pyright: ignore[reportUnknownVariableType]
            elif isinstance(result, ObservableProxy):
                result = result.unwrap()  # pyright: ignore[reportUnknownVariableType]
            elif isinstance(result, ObservableDict):
                result = result.to_dict()  # pyright: ignore[reportUnknownVariableType]
            elif isinstance(result, ObservableList):
                result = result.to_list()  # pyright: ignore[reportUnknownVariableType]

            return result  # pyright: ignore[reportUnknownVariableType]
        except Exception:
            return None

    # Evaluate the expression to get initial value
    initial_value = evaluate_expression()

    # Determine if this is a valid collection for model binding
    # For QTreeView with children=, a single object is valid (tree root)
    is_tree_with_children = is_tree_view_fn(widget_instance) and field_info.tree_children is not None

    # Convert result to collection format
    def to_collection(value: Any) -> list[Any] | None:
        """Convert value to a list for model binding."""
        if value is None:
            return []
        if isinstance(value, ObservableList):
            return list(cast(ObservableList[Any], value))
        if isinstance(value, list):
            return list(cast(list[Any], value))
        if isinstance(value, ObservableDict):
            return list(cast(ObservableDict[Any, Any], value).to_dict().items())
        if isinstance(value, dict):
            return list(cast(dict[Any, Any], value).items())
        # For QTreeView with children=, single object is valid (tree root)
        if is_tree_with_children:
            return [value]
        # Non-collection, non-tree - not valid for model binding
        return None

    collection = to_collection(initial_value)
    if collection is None:
        return False

    # Create a managed ObservableList to hold the data
    managed_list: ObservableList[Any] = ObservableList(collection)

    # Subscribe to source observables to update the managed list
    updating = {"flag": False}

    def on_source_change(*_: Any) -> None:
        if updating["flag"]:
            return

        # Check if widget's C++ object is still valid
        try:
            from shiboken6 import isValid

            if not isValid(widget_instance):
                return
        except ImportError:
            pass
        except RuntimeError:
            return

        updating["flag"] = True
        try:
            new_value = evaluate_expression()
            new_collection = to_collection(new_value)
            if new_collection is not None:
                # Update the managed list
                managed_list.clear()
                managed_list.extend(new_collection)
        finally:
            updating["flag"] = False

    # Subscribe to all source observables
    subscribed: set[int] = set()
    for obs in all_observables:
        obs_id = id(obs)
        if obs_id not in subscribed:
            subscribed.add(obs_id)
            obs.on_change(on_source_change)

    # Apply the model binding using the managed list
    return apply_model_binding(
        host,
        widget_instance,
        managed_list,
        f"__expr__{expression}__",
        field_info,
        is_table_view_fn=is_table_view_fn,
        is_tree_view_fn=is_tree_view_fn,
        resolve_or_create_variable_fn=resolve_or_create_variable_fn,
    )
