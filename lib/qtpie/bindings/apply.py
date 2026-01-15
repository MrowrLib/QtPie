"""Shared binding application logic for Widget and Window."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, cast

from observant import Observable, ObservableList, ObservableProxy
from qtpy.QtWidgets import QWidget

logger = logging.getLogger("qtpie.bindings")

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.new_field import NewField


def _is_enum_class(value: Any) -> bool:
    """Check if value is an Enum class (not an instance)."""
    try:
        return isinstance(value, type) and issubclass(value, Enum)
    except TypeError:
        return False


class BindingConfig(Protocol):
    """Protocol for config objects that support bindings."""

    fields: dict[str, NewField]
    auto_bind: bool
    widget_props: dict[str, Any]


def _is_model_widget(widget: QWidget) -> bool:
    """Check if widget supports setModel() - e.g., QComboBox, QListView, QTableView."""
    set_model = getattr(widget, "setModel", None)
    return set_model is not None and callable(set_model)


def _is_table_view(widget: QWidget) -> bool:
    """Check if widget is a QTableView (needs ReactiveTableModel)."""
    from qtpy.QtWidgets import QTableView

    return isinstance(widget, QTableView)


def _is_tree_view(widget: QWidget) -> bool:
    """Check if widget is a QTreeView (needs ReactiveTreeModel)."""
    from qtpy.QtWidgets import QTreeView

    return isinstance(widget, QTreeView)


def pre_create_selection_variables(host: QWidget, config: BindingConfig) -> None:
    """Pre-create Variables for selection bindings that reference bare Variable[T] annotations.

    This allows `_index: Variable[int]` (no new()) to work with selectedIndex="_index".
    Must be called BEFORE binding application.

    Works with both Widget and App configs.
    """
    from observant import Observable

    from qtpie.state import QtPieState
    from qtpie.variable import Variable as VarType
    from qtpie.variable import _RequiredBindingDescriptor, _VariableDescriptor  # pyright: ignore[reportPrivateUsage]

    # Get required bindings from config
    required_bindings: set[str] = getattr(config, "required_bindings", set())
    if not required_bindings:
        return

    # Find which required bindings are used as selection bindings
    all_selection_paths: set[str] = set()
    for field_info in config.fields.values():
        # QComboBox/QListView bindings
        if field_info.selected_index is not None:
            all_selection_paths.add(field_info.selected_index.lstrip("_"))
        if field_info.selected_item is not None:
            all_selection_paths.add(field_info.selected_item.lstrip("_"))
        # QListView multi selection bindings
        if field_info.selected_indexes is not None:
            all_selection_paths.add(field_info.selected_indexes.lstrip("_"))
        if field_info.selected_items_list is not None:
            all_selection_paths.add(field_info.selected_items_list.lstrip("_"))
        # QTableView single selection bindings
        if field_info.selected_row is not None:
            all_selection_paths.add(field_info.selected_row.lstrip("_"))
        if field_info.selected_column is not None:
            all_selection_paths.add(field_info.selected_column.lstrip("_"))
        if field_info.selected_cell is not None:
            all_selection_paths.add(field_info.selected_cell.lstrip("_"))
        # QTableView multi selection bindings
        if field_info.selected_rows is not None:
            all_selection_paths.add(field_info.selected_rows.lstrip("_"))
        if field_info.selected_columns is not None:
            all_selection_paths.add(field_info.selected_columns.lstrip("_"))
        if field_info.selected_cells is not None:
            all_selection_paths.add(field_info.selected_cells.lstrip("_"))
        if field_info.selected_items is not None:
            all_selection_paths.add(field_info.selected_items.lstrip("_"))
        # Note: QTreeView uses selected_item and selected_items which are already
        # handled above (shared with QComboBox/QListView/QTableView)
        # Dock group selection binding
        if field_info.dock_group_selected_index is not None:
            all_selection_paths.add(field_info.dock_group_selected_index.lstrip("_"))

    # Also check Variable[T, Dock[W]] and Variable[list[T], Dock[W]] fields
    # These store dock_info on the _VariableDescriptor, not in config.fields
    variable_dock_fields: list[str] = getattr(config, "variable_dock_fields", [])
    for field_name in variable_dock_fields:
        descriptor = getattr(type(host), field_name, None)
        if isinstance(descriptor, _VariableDescriptor) and descriptor.dock_info:
            dock_info = descriptor.dock_info
            # Check for selection bindings in dock_info
            if dock_info.get("selected_index"):
                all_selection_paths.add(dock_info["selected_index"].lstrip("_"))
            if dock_info.get("selected_item"):
                all_selection_paths.add(dock_info["selected_item"].lstrip("_"))
            if dock_info.get("dock_group_selected_index"):
                all_selection_paths.add(dock_info["dock_group_selected_index"].lstrip("_"))

    if not all_selection_paths:
        return

    # Ensure _qtpie state exists
    state = getattr(host, "_qtpie", None)
    if state is None:
        state = QtPieState(host)
        host._qtpie = state  # type: ignore[attr-defined]

    # Create Variables for required bindings that are used as selection bindings
    for name in list(required_bindings):
        lookup_name = name.lstrip("_")
        if lookup_name not in all_selection_paths:
            continue

        # Check if already created
        if name in state.variables:
            continue

        # Get the descriptor to find the inner type
        cls_attr = getattr(type(host), name, None)
        if isinstance(cls_attr, _RequiredBindingDescriptor):
            # For selection bindings, always use Observable(None)
            # The value will be synced from the widget's current selection
            wrapper = Observable(None)
            var: VarType[Any] = VarType(wrapper)
            state.register_variable(name, var)


def _resolve_or_create_variable(
    host: QWidget,
    path: str,
    inner_type: type | None = None,
) -> Any:
    """Resolve a binding path to a Variable, creating one if it's a bare annotation.

    For bare `Variable[T]` annotations (no `= new()`), this will create the Variable
    on-the-fly with a None default, allowing it to sync from the widget.

    Also searches the parent widget hierarchy for matching Variables.

    Args:
        host: The Widget/Window instance
        path: The binding path (e.g., "_index")
        inner_type: The inner type for the Variable if we need to create it (unused for selection bindings)

    Returns:
        The Variable instance, or None if not found/creatable.
    """
    from observant import Observable

    from qtpie.bindings import resolve_binding_source
    from qtpie.state import QtPieState
    from qtpie.variable import Variable as VarType
    from qtpie.variable import (
        _RequiredBindingDescriptor,  # pyright: ignore[reportPrivateUsage]
        _try_get_variable,  # pyright: ignore[reportPrivateUsage]
    )

    # First try normal resolution on host
    source = resolve_binding_source(host, path)  # type: ignore[arg-type]
    if isinstance(source, VarType):
        return source
    # Also return Observable/ObservableProxy sources (e.g., record enum fields)
    if isinstance(source, (Observable, ObservableProxy)):
        return source

    # Check for bare Variable[T] annotation (using _RequiredBindingDescriptor)
    # Strip leading underscores for lookup
    lookup_name = path.lstrip("_")
    underscore_name = f"_{lookup_name}"

    # Check both the exact name and underscore-prefixed name on host
    for attr_name in [lookup_name, underscore_name]:
        cls_attr = getattr(type(host), attr_name, None)
        if isinstance(cls_attr, _RequiredBindingDescriptor):
            # Found a required binding - create the Variable now
            if not hasattr(host, "_qtpie"):
                host._qtpie = QtPieState(host)  # type: ignore[attr-defined]

            qtpie_state = host._qtpie  # type: ignore[attr-defined]

            # For selection bindings, always use Observable(None)
            # The value will be synced from the widget's current selection
            # We can't use _create_observable_for_type because it tries to instantiate complex types
            wrapper = Observable(None)
            var: VarType[Any] = VarType(wrapper)
            qtpie_state.register_variable(attr_name, var)  # pyright: ignore[reportUnknownMemberType]

            return var

    # Try to find Variable in parent hierarchy (for selection bindings to parent Variables)
    from qtpy.QtWidgets import QApplication

    current: Any = host
    while True:
        if not hasattr(current, "parent") or not callable(current.parent):
            break
        parent: Any = current.parent()
        if parent is None:
            break

        # Try both the original path and underscore variants
        for attr_name in [path, lookup_name, underscore_name]:
            found = _try_get_variable(parent, attr_name)
            if found is not None:
                return found

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        for attr_name in [path, lookup_name, underscore_name]:
            found = _try_get_variable(app, attr_name)
            if found is not None:
                return found

    return None


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
    from qtpie.bindings.model_binding import apply_model_binding
    from qtpie.bindings.tab_binding import apply_tab_widget_bindings
    from qtpie.translations.translatable import Translatable
    from qtpie.variable import Variable as VarType

    for name, field_info in config.fields.items():
        # Skip list widget fields
        if field_info.is_list_widget:
            continue

        # Get the widget instance
        widget_instance = getattr(host, name, None)
        if widget_instance is None or not isinstance(widget_instance, QWidget):
            continue

        # Handle QTabWidget with tabs= binding
        if field_info.is_tab_widget and field_info.tabs is not None:
            apply_tab_widget_bindings(host, widget_instance, field_info)
            continue

        # Determine bind path - may be string, Translatable, or Enum class
        bind_value = field_info.bind
        translatable: Translatable | None = None

        # Handle Enum class binding: bind=Priority creates list from enum members
        if _is_enum_class(bind_value) and _is_model_widget(widget_instance):
            # Create ObservableList from enum members
            enum_class = cast("type[Enum]", bind_value)
            enum_members = list(enum_class)
            obs_list: ObservableList[Any] = ObservableList(enum_members)

            # Set default format to {name} if not provided (shows enum name like "LOW", "HIGH")
            if field_info.model_format is None:
                field_info.model_format = "{name}"

            # Apply model binding with the enum list as source
            apply_model_binding(
                host,
                widget_instance,
                obs_list,
                f"__enum__{enum_class.__name__}",
                field_info,
                is_table_view_fn=_is_table_view,
                is_tree_view_fn=_is_tree_view,
                resolve_or_create_variable_fn=_resolve_or_create_variable,
            )
            continue

        if isinstance(bind_value, Translatable):
            # Resolve translatable to get format string
            translatable = bind_value
            bind_path = translatable.resolve()
        elif bind_value is not None:
            bind_path = bind_value
        elif config.auto_bind:
            bind_path = name.lstrip("_")
        else:
            continue

        # Handle format strings
        # Also handle nested paths for NON-record widgets (paths like "parent_var.field")
        # because ObservableProxy creates new Observables for each path lookup.
        # But DON'T convert nested paths for Widget[T] record bindings - those should use
        # the existing record binding code path which handles optional chaining properly.
        is_nested_path = "." in bind_path.replace("?.", ".")

        # Check if this is a record binding (Widget[T] with a record type)
        has_record = hasattr(config, "record_type") and config.record_type is not None  # type: ignore[union-attr]

        # For record bindings, only use format binding if it's explicitly a format string
        # For non-record widgets, convert nested paths to format bindings for parent hierarchy lookup
        use_format_binding = is_format_string(bind_path) or (is_nested_path and not has_record and not _is_model_widget(widget_instance))
        format_template = bind_path if is_format_string(bind_path) else f"{{{bind_path}}}" if use_format_binding and is_nested_path else None

        if use_format_binding and (is_format_string(bind_path) or format_template is not None):
            from qtpie.bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                setter = adapter.setter

                def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def setter_fn(val: Any) -> None:
                        s(w, val)  # noqa: B023 - val is parameter, not loop var

                    return setter_fn

                widget_setter = make_setter(setter, widget_instance)
                create_format_binding(host, bind_path if is_format_string(bind_path) else format_template, widget_setter)  # type: ignore[arg-type]

                # Register for hot-reload if this was a Translatable
                if translatable is not None:
                    from qtpie.translations.store import register_format_binding

                    register_format_binding(
                        widget_instance,
                        default_prop,
                        translatable.text,
                        translatable.context,
                        host,  # type: ignore[arg-type]
                        widget_setter,
                    )
            continue

        # Resolve the binding source
        source = resolve_binding_source(host, bind_path)  # type: ignore[arg-type]
        if source is None:
            # Source not found - might not be parented yet
            # Schedule deferred retry for model widgets
            if _is_model_widget(widget_instance):
                from qtpy.QtCore import QTimer

                def make_deferred_model_bind(w: QWidget, h: QWidget, bp: str, fi: Any) -> Callable[[], None]:
                    def retry_bind() -> None:
                        # Re-attempt resolution after parenting
                        deferred_source = resolve_binding_source(h, bp)  # type: ignore[arg-type]
                        if deferred_source is not None:
                            apply_model_binding(
                                h,
                                w,
                                deferred_source,
                                bp,
                                fi,
                                is_table_view_fn=_is_table_view,
                                is_tree_view_fn=_is_tree_view,
                                resolve_or_create_variable_fn=_resolve_or_create_variable,
                            )

                    return retry_bind

                QTimer.singleShot(0, make_deferred_model_bind(widget_instance, host, bind_path, field_info))
            continue

        # Check if this is a model widget (QComboBox, QListView, etc.) with a list source
        if _is_model_widget(widget_instance):
            if apply_model_binding(
                host,
                widget_instance,
                source,
                bind_path,
                field_info,
                is_table_view_fn=_is_table_view,
                is_tree_view_fn=_is_tree_view,
                resolve_or_create_variable_fn=_resolve_or_create_variable,
            ):
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
                # Flag to prevent circular updates (Observable → Widget → Observable)
                updating: dict[str, bool] = {"flag": False}

                # Set initial value
                adapter.setter(widget_instance, source.get())

                # Subscribe to Observable changes
                setter = adapter.setter

                def make_obs_to_widget(s: Callable[[Any, Any], None], w: QWidget, upd: dict[str, bool]) -> Callable[[Any], None]:
                    def on_observable_change(v: Any) -> None:
                        if upd["flag"]:
                            return
                        upd["flag"] = True
                        try:
                            s(w, v)
                        finally:
                            upd["flag"] = False

                    return on_observable_change

                source.on_change(make_obs_to_widget(setter, widget_instance, updating))

                # Two-way binding: Widget → Observable
                if adapter.signal_name is not None and adapter.getter is not None:
                    signal = getattr(widget_instance, adapter.signal_name, None)
                    getter = adapter.getter

                    def make_widget_to_obs(obs: Observable[Any], g: Callable[[Any], Any], w: QWidget, upd: dict[str, bool]) -> Callable[[], None]:
                        def on_widget_change() -> None:
                            if upd["flag"]:
                                return
                            upd["flag"] = True
                            try:
                                obs.set(g(w))
                            finally:
                                upd["flag"] = False

                        return on_widget_change

                    if signal is not None:
                        signal.connect(make_widget_to_obs(source, getter, widget_instance, updating))


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

    For props like windowTitle="{title}" or windowTitle=t("My App"), creates bindings.
    """
    from qtpie.bindings import create_format_binding, is_format_string
    from qtpie.translations.translatable import Translatable

    for prop_name, value in config.widget_props.items():
        translatable: Translatable | None = None
        template: str | None = None

        # Handle Translatable objects
        if isinstance(value, Translatable):
            translatable = value
            template = translatable.resolve()
        elif isinstance(value, str) and is_format_string(value):
            template = value
        else:
            continue

        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter_method = getattr(host, setter_name, None)
        if setter_method is None or not callable(setter_method):
            raise AttributeError(f"{type(host).__name__} has no setter '{setter_name}' for property '{prop_name}'")

        # If it's a format string, create format binding
        if is_format_string(template):
            create_format_binding(host, template, setter_method)  # type: ignore[arg-type]
        else:
            # Static translated text - just set it
            setter_method(template)

        # Register for hot-reload if this was a Translatable
        if translatable is not None:
            from qtpie.translations.store import register_format_binding

            register_format_binding(
                host,
                prop_name,
                translatable.text,
                translatable.context,
                host,  # type: ignore[arg-type]
                setter_method,  # type: ignore[arg-type]
            )
