"""Shared binding application logic for Widget and Window."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from observant import Observable, ObservableList
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.new_field import NewField


class BindingConfig(Protocol):
    """Protocol for config objects that support bindings."""

    fields: dict[str, NewField]
    auto_bind: bool
    widget_props: dict[str, Any]


def _is_model_widget(widget: QWidget) -> bool:
    """Check if widget supports setModel() - e.g., QComboBox, QListView, QTableView."""
    set_model = getattr(widget, "setModel", None)
    return set_model is not None and callable(set_model)


def pre_create_selection_variables(host: QWidget, config: BindingConfig) -> None:
    """Pre-create Variables for selection bindings that reference bare Variable[T] annotations.

    This allows `_index: Variable[int]` (no new()) to work with selectedIndex="_index".
    Must be called BEFORE binding application.

    Works with both Widget and App configs.
    """
    from observant import Observable

    from qtpie.state import QtPieState
    from qtpie.variable import Variable as VarType
    from qtpie.variable import _RequiredBindingDescriptor  # pyright: ignore[reportPrivateUsage]

    # Get required bindings from config
    required_bindings: set[str] = getattr(config, "required_bindings", set())
    if not required_bindings:
        return

    # Find which required bindings are used as selection bindings
    all_selection_paths: set[str] = set()
    for field_info in config.fields.values():
        if field_info.selected_index is not None:
            all_selection_paths.add(field_info.selected_index.lstrip("_"))
        if field_info.selected_item is not None:
            all_selection_paths.add(field_info.selected_item.lstrip("_"))

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
    from qtpie.variable import _RequiredBindingDescriptor  # pyright: ignore[reportPrivateUsage]

    # First try normal resolution
    source = resolve_binding_source(host, path)  # type: ignore[arg-type]
    if isinstance(source, VarType):
        return source

    # Check for bare Variable[T] annotation (using _RequiredBindingDescriptor)
    # Strip leading underscores for lookup
    lookup_name = path.lstrip("_")
    underscore_name = f"_{lookup_name}"

    # Check both the exact name and underscore-prefixed name
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

    return None


def _setup_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveListModel
    selected_index_path: str | None,
    selected_item_path: str | None,
) -> None:
    """Set up two-way selection bindings for model widgets.

    Args:
        host: The Widget/Window instance containing the Variables
        widget: The model widget (QComboBox, QListView, etc.)
        model: The ReactiveListModel backing the widget
        selected_index_path: Variable path for index binding (e.g., "_selected_idx")
        selected_item_path: Variable path for item binding (e.g., "_selected_item")
    """
    if selected_index_path is None and selected_item_path is None:
        return

    from qtpy.QtCore import Qt

    from qtpie.variable import Variable as VarType

    # Resolve the Variables (creating them if they're bare annotations)
    index_var: VarType[int] | None = None
    item_var: VarType[Any] | None = None

    if selected_index_path is not None:
        source = _resolve_or_create_variable(host, selected_index_path, int)
        if isinstance(source, VarType):
            index_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_item_path is not None:
        source = _resolve_or_create_variable(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Get widget methods for index-based selection (works for QComboBox)
    set_current_index_fn = getattr(widget, "setCurrentIndex", None)
    current_index_changed = getattr(widget, "currentIndexChanged", None)

    # Helper to get item at index via model's UserRole
    def get_item_at_index(idx: int) -> Any:
        if idx < 0 or idx >= model.rowCount():
            return None
        model_index = model.index(idx, 0)
        return model.data(model_index, Qt.ItemDataRole.UserRole)

    # Helper to find index of item
    def find_index_of_item(item: Any) -> int:
        for i in range(model.rowCount()):
            if get_item_at_index(i) == item:
                return i
        return -1

    # Sync initial values between Variables and widget
    current_widget_index_fn = getattr(widget, "currentIndex", None)

    # Get the current widget index (will sync Variables from this if they're None)
    current_widget_idx = current_widget_index_fn() if current_widget_index_fn else 0

    if index_var is not None and set_current_index_fn is not None:
        initial_idx = index_var.value
        # Variable[int] can have None value if no default provided
        if initial_idx is not None:  # pyright: ignore[reportUnnecessaryComparison]
            set_current_index_fn(initial_idx)
            current_widget_idx = initial_idx  # Update for item_var sync below
        else:
            # Sync Variable to widget's current state
            index_var.value = current_widget_idx

    if item_var is not None:
        initial_item = item_var.value
        if initial_item is not None:
            # Set widget to match item if index didn't already set it
            if index_var is None and set_current_index_fn is not None:
                idx = find_index_of_item(initial_item)
                if idx >= 0:
                    set_current_index_fn(idx)
        else:
            # Sync item Variable to widget's current selection
            item_var.value = get_item_at_index(current_widget_idx)

    # Variable → Widget binding (and cross-update between index/item vars)
    if index_var is not None and set_current_index_fn is not None:

        def on_index_var_change(new_idx: int) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                set_current_index_fn(new_idx)
                # Also update item_var if both bindings are present
                if item_var is not None:
                    item_var.value = get_item_at_index(new_idx)
            finally:
                updating["flag"] = False

        index_var.on_change(on_index_var_change)

    if item_var is not None and set_current_index_fn is not None:

        def on_item_var_change(*_args: Any) -> None:
            # Note: Observable passes value, ObservableProxy passes nothing
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                new_item = item_var.value  # type: ignore[union-attr]
                idx = find_index_of_item(new_item)
                if idx >= 0:
                    set_current_index_fn(idx)
                    # Also update index_var if both bindings are present
                    if index_var is not None:
                        index_var.value = idx
            finally:
                updating["flag"] = False

        item_var.on_change(on_item_var_change)

    # Widget → Variable binding
    if current_index_changed is not None and (index_var is not None or item_var is not None):

        def on_widget_selection_changed(new_idx: int) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                if index_var is not None:
                    index_var.value = new_idx
                if item_var is not None:
                    item_var.value = get_item_at_index(new_idx)
            finally:
                updating["flag"] = False

        current_index_changed.connect(on_widget_selection_changed)


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

        # Determine bind path - may be string or Translatable
        bind_value = field_info.bind
        translatable: Translatable | None = None

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

                widget_setter = make_setter(setter, widget_instance)
                create_format_binding(host, bind_path, widget_setter)  # type: ignore[arg-type]

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
            continue

        # Check if this is a model widget (QComboBox, QListView, etc.) with a list source
        if _is_model_widget(widget_instance):
            obs_list: ObservableList[Any] | None = None

            # Extract ObservableList from Variable or use directly
            if isinstance(source, VarType):
                wrapper = source.observable
                if isinstance(wrapper, ObservableList):
                    obs_list = wrapper
            elif isinstance(source, ObservableList):
                obs_list = source

            if obs_list is not None:
                # Create ReactiveListModel and set it on the widget
                from qtpie.bindings.format_binding import create_item_formatter
                from qtpie.models import ReactiveListModel

                # Check for format= to customize item display
                format_fn = None
                if field_info.model_format is not None:
                    format_fn = create_item_formatter(field_info.model_format)

                model = ReactiveListModel(obs_list, parent=widget_instance, format_fn=format_fn)
                widget_instance.setModel(model)  # type: ignore[attr-defined]

                # Set up selection bindings if specified
                _setup_selection_bindings(
                    host,
                    widget_instance,
                    model,
                    field_info.selected_index,
                    field_info.selected_item,
                )
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
