"""Tab widget bindings for QTabWidget."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from observant import ObservableDict, ObservableList
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    pass


def _recreate_list_widget_fields_for_record(
    child: Any,  # Widget[T]
    child_config: Any,  # _QtPieConfig
    host_record: Any,  # RecordVariable
) -> None:
    """Recreate list widget fields that were bound to stale record data.

    When a child Widget[T] is created as a tab, it may create list widget fields
    (list[QLabel] = new(bind="headers")) using its own default record, which may
    have empty values. After the parent's record is propagated, we need to recreate
    these fields with the actual data.
    """
    from observant import ObservableDict, ObservableList

    from qtpie.dict_widget_repeater import DictWidgetRepeater
    from qtpie.widget_repeater import WidgetRepeater

    # Get the actual record target
    target = object.__getattribute__(host_record.observable, "_target")
    if target is None:
        return

    for name, field in child_config.fields.items():
        if not field.is_list_widget:
            continue

        # Check if this field is bound to a record property
        if field.bind is None:
            continue

        bind_path = field.bind.lstrip("_")

        # Check if the bind path exists on the record
        if not hasattr(target, bind_path):
            continue

        # Get the existing field (may be NewField or existing repeater)
        existing = getattr(child, name, None)
        if existing is None:
            continue

        # Get the new data from the record
        new_data = getattr(target, bind_path)
        if new_data is None:
            continue

        # Get computed object name
        if field.object_name is not None:
            computed_object_name = field.object_name
        elif child_config.object_name is not None:
            computed_object_name = child_config.object_name
        else:
            computed_object_name = name[1:] if name.startswith("_") else name

        # Recreate the repeater with new data
        if isinstance(new_data, dict):
            obs_dict: ObservableDict[Any, Any] = ObservableDict(cast(dict[Any, Any], new_data))
            setattr(child, field.bind, obs_dict)
            bind_expr = field.list_format if field.list_format is not None else "{#key} = {#value}"

            dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
                observable_dict=obs_dict,
                key_type=None,
                value_type=None,
                widget_type=field.list_widget_type,
                widget_args=field.args,
                widget_kwargs=field.kwargs,
                widget_props=field.widget_props,
                bind_expr=bind_expr,
                sort=field.sort,
                object_name=computed_object_name,
                css_classes=field.css_classes,
                signal_connections=field.signal_connections,
                parent_widget=child,
            )
            setattr(child, name, dict_repeater)

        elif isinstance(new_data, list):
            obs_list: ObservableList[Any] = ObservableList(cast(list[Any], new_data))
            setattr(child, field.bind, obs_list)
            bind_expr = field.list_format if field.list_format is not None else "{#self}"

            list_repeater: WidgetRepeater[Any] = WidgetRepeater(
                observable_list=obs_list,
                item_type=None,
                widget_type=field.list_widget_type,
                widget_args=field.args,
                widget_kwargs=field.kwargs,
                widget_props=field.widget_props,
                bind_expr=bind_expr,
                sort=field.sort,
                object_name=computed_object_name,
                css_classes=field.css_classes,
                signal_connections=field.signal_connections,
                parent_widget=child,
            )
            setattr(child, name, list_repeater)


def _propagate_record_to_child(host: QWidget, child: QWidget) -> None:
    """Propagate host's record to a child Widget[T] if types match.

    When a Widget[T] contains child Widget[T] widgets (same T), the children
    should share the parent's record. This handles widgets created dynamically
    via tabs= which don't go through the normal NewField auto-record-bind flow.
    """
    from qtpie.bindings.apply import apply_auto_bindings
    from qtpie.variable import RecordVariable

    # Check if host has a record type
    host_config = getattr(type(host), "_qtpie_config", None)
    if host_config is None:
        return
    host_record_type = getattr(host_config, "record_type", None)
    if host_record_type is None:
        return

    # Check if child has a matching record type
    child_config = getattr(type(child), "_qtpie_config", None)
    if child_config is None:
        return
    child_record_type = getattr(child_config, "record_type", None)
    if child_record_type is None:
        return

    # Types must match
    if host_record_type != child_record_type:
        return

    # Share host's record with child
    host_record = getattr(host, "record", None)
    if host_record is not None and isinstance(host_record, RecordVariable):
        child_record_var: RecordVariable[Any] = RecordVariable(host_record.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        child.record = child_record_var  # type: ignore[union-attr]
        # Re-apply bindings on child now that record is set
        apply_auto_bindings(child, child_config)  # type: ignore[arg-type]

        # Recreate list widget fields that may have been created with stale record data
        # When child was first created, it may have used a default record with empty values.
        # Now that we've propagated the actual record, we need to recreate the list widgets.
        _recreate_list_widget_fields_for_record(child, child_config, host_record)  # type: ignore[arg-type]

        # Process any pending list widget fields that were deferred during __init__
        pending_fields: list[str] | None = getattr(child, "_qtpie_pending_list_fields", None)
        if pending_fields:
            from qtpie.widget import _create_list_widget_fields  # type: ignore[reportPrivateUsage]

            _create_list_widget_fields(child, child_config)  # type: ignore[arg-type]
            # Clear pending list
            child._qtpie_pending_list_fields = []  # type: ignore[attr-defined]

        # Apply model bindings (QTableView, QListView, etc.) now that record is set
        from qtpie.widget import _apply_model_bindings_for_record  # type: ignore[reportPrivateUsage]

        _apply_model_bindings_for_record(child, child_config)  # type: ignore[arg-type]


def _set_tabs_from_dict(
    tab_widget: Any,  # QTabWidget
    tabs: dict[str, type[QWidget]],
) -> dict[str, QWidget]:
    """Populate QTabWidget from dict. Returns name -> widget mapping."""
    tab_widget.clear()
    tab_widgets: dict[str, QWidget] = {}
    for name, widget_type in tabs.items():
        widget = widget_type(parent=tab_widget)
        tab_widgets[name] = widget
        tab_widget.addTab(widget, name)
    return tab_widgets


def _set_tabs_from_list(
    tab_widget: Any,  # QTabWidget
    tabs: list[type[QWidget]],
) -> dict[str, QWidget]:
    """Populate QTabWidget from list. Names from windowTitle() or class name."""
    tab_widget.clear()
    tab_widgets: dict[str, QWidget] = {}
    for widget_type in tabs:
        widget = widget_type(parent=tab_widget)
        name = widget.windowTitle() or widget_type.__name__  # Fallback to class name
        tab_widgets[name] = widget
        tab_widget.addTab(widget, name)
    return tab_widgets


def _resolve_widget_from_field(host: QWidget, field_name: str) -> QWidget | None:
    """Resolve a widget from a field name on the host.

    Handles:
    - Regular widget fields: returns the widget
    - Variable[T, W]: returns .widget
    - Variable[T, Dock[W]]: returns .widget.widget (the inner content widget)
    """
    if not hasattr(host, field_name):
        return None

    field_value = getattr(host, field_name)

    # Check if it's a Variable with a widget
    if hasattr(field_value, "widget"):
        widget = field_value.widget
        # Check if it's a Dock (Variable[T, Dock[W]])
        if hasattr(widget, "widget"):
            # It's a Dock, get the inner widget
            return widget.widget  # type: ignore[no-any-return]
        return widget  # type: ignore[no-any-return]

    # Regular widget field
    if isinstance(field_value, QWidget):
        return field_value

    return None


def _set_tabs_from_normalized(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    tabs: list[dict[str, Any]],
) -> dict[str, QWidget]:
    """Populate QTabWidget from normalized tab definitions.

    Tab definitions are dicts with:
    - {"type": "class", "cls": WidgetClass, "name": "TabName" | None}
    - {"type": "ref", "field": "field_name", "name": "TabName" | None}
    """
    tab_widget.clear()
    tab_widgets: dict[str, QWidget] = {}

    for tab_def in tabs:
        tab_type = tab_def.get("type")
        explicit_name = tab_def.get("name")

        if tab_type == "class":
            # Create new widget instance
            widget_cls = tab_def["cls"]
            widget = widget_cls(parent=tab_widget)
            # Propagate host's record to child Widget[T] if types match
            _propagate_record_to_child(host, widget)
            # Name: explicit > windowTitle > class name
            name = explicit_name or widget.windowTitle() or widget_cls.__name__

        elif tab_type == "ref":
            # Reference existing widget by field name
            field_name = tab_def["field"]
            widget = _resolve_widget_from_field(host, field_name)
            if widget is None:
                continue  # Skip if field not found
            # Name: explicit > windowTitle > field name
            name = explicit_name or widget.windowTitle() or field_name

        else:
            continue  # Unknown type

        tab_widgets[name] = widget
        tab_widget.addTab(widget, name)

    return tab_widgets


def _bind_tab_widget_to_dict(
    tab_widget: Any,  # QTabWidget
    obs: ObservableDict[str, type[QWidget]],
    tab_widgets: dict[str, QWidget],
) -> None:
    """Bind QTabWidget to ObservableDict for granular reactive updates."""

    def on_insert(key: str, value: type[QWidget]) -> None:
        widget = value(parent=tab_widget)
        tab_widgets[key] = widget
        tab_widget.addTab(widget, key)

    def on_remove(key: str, _value: type[QWidget]) -> None:
        if key in tab_widgets:
            widget = tab_widgets.pop(key)
            idx = tab_widget.indexOf(widget)
            if idx >= 0:
                tab_widget.removeTab(idx)

    def on_replace(key: str, old: type[QWidget], new: type[QWidget]) -> None:
        on_remove(key, old)
        on_insert(key, new)

    def on_clear(_items: dict[str, type[QWidget]]) -> None:
        tab_widget.clear()
        tab_widgets.clear()

    obs.on_insert(on_insert)
    obs.on_remove(on_remove)
    obs.on_replace(on_replace)
    obs.on_clear(on_clear)


def _bind_tab_widget_to_list(
    tab_widget: Any,  # QTabWidget
    obs: ObservableList[type[QWidget]],
    tab_widgets: dict[str, QWidget],
) -> None:
    """Bind QTabWidget to ObservableList for granular reactive updates."""
    # Track widgets by index for proper removal
    widgets_by_index: list[QWidget] = list(tab_widgets.values())

    def on_insert(index: int, value: type[QWidget]) -> None:
        widget = value(parent=tab_widget)
        name = widget.windowTitle() or value.__name__
        widgets_by_index.insert(index, widget)
        tab_widgets[name] = widget
        tab_widget.insertTab(index, widget, name)

    def on_remove(index: int, _value: type[QWidget]) -> None:
        if 0 <= index < len(widgets_by_index):
            widget = widgets_by_index.pop(index)
            # Remove from name mapping
            for name, w in list(tab_widgets.items()):
                if w is widget:
                    del tab_widgets[name]
                    break
            tab_widget.removeTab(index)

    def on_replace(index: int, old: type[QWidget], new: type[QWidget]) -> None:
        on_remove(index, old)
        on_insert(index, new)

    def on_clear(_items: list[type[QWidget]]) -> None:
        tab_widget.clear()
        tab_widgets.clear()
        widgets_by_index.clear()

    obs.on_insert(on_insert)
    obs.on_remove(on_remove)
    obs.on_replace(on_replace)
    obs.on_clear(on_clear)


def _setup_tab_index_binding(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    var_name: str,
) -> None:
    """Set up two-way binding for selectedIndex."""
    from qtpie.bindings import resolve_binding_source
    from qtpie.variable import Variable as VarType

    source = resolve_binding_source(host, var_name)  # type: ignore[arg-type]
    if not isinstance(source, VarType):
        return

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Variable -> Tab
    def update_tab(value: int) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            if tab_widget.currentIndex() != value:
                tab_widget.setCurrentIndex(value)
        finally:
            updating["flag"] = False

    source.on_change(update_tab)

    # Initial sync
    initial_value = source.value
    if initial_value is not None:  # pyright: ignore[reportUnnecessaryComparison]
        tab_widget.setCurrentIndex(initial_value)
    else:
        # Sync Variable from widget's current state
        source.value = tab_widget.currentIndex()

    # Tab -> Variable
    def on_tab_changed(index: int) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            if source.value != index:
                source.value = index
        finally:
            updating["flag"] = False

    tab_widget.currentChanged.connect(on_tab_changed)


def _setup_tab_widget_binding(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    var_name: str,
) -> None:
    """Set up binding for selectedWidget (widget reference tracking)."""
    from qtpie.bindings import resolve_binding_source
    from qtpie.variable import Variable as VarType

    source = resolve_binding_source(host, var_name)  # type: ignore[arg-type]
    if not isinstance(source, VarType):
        return

    # Tab -> Variable (widget reference)
    def on_tab_changed(index: int) -> None:
        widget = tab_widget.widget(index)
        if source.value is not widget:
            source.value = widget

    tab_widget.currentChanged.connect(on_tab_changed)

    # Initial sync
    current_idx = tab_widget.currentIndex()
    if current_idx >= 0:
        source.value = tab_widget.widget(current_idx)


def apply_tab_widget_bindings(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    field_info: Any,  # NewField
) -> None:
    """Apply tabs= and selection bindings to QTabWidget."""
    from qtpie.bindings import resolve_binding_source
    from qtpie.variable import Variable as VarType

    tabs_source = field_info.tabs
    tab_widgets: dict[str, QWidget] = {}

    if isinstance(tabs_source, str):
        # Variable reference - resolve and bind reactively
        source = resolve_binding_source(host, tabs_source)  # type: ignore[arg-type]
        if isinstance(source, VarType):
            obs = source.observable
            if isinstance(obs, ObservableDict):
                # Initial population from dict
                initial_value = obs.to_dict()
                tab_widgets = _set_tabs_from_dict(tab_widget, initial_value)  # pyright: ignore[reportArgumentType]
                # Subscribe for reactive updates
                _bind_tab_widget_to_dict(tab_widget, obs, tab_widgets)  # pyright: ignore[reportArgumentType]
            elif isinstance(obs, ObservableList):
                # Initial population from list
                initial_value = obs.to_list()
                tab_widgets = _set_tabs_from_list(tab_widget, initial_value)  # pyright: ignore[reportArgumentType]
                # Subscribe for reactive updates
                _bind_tab_widget_to_list(tab_widget, obs, tab_widgets)  # pyright: ignore[reportArgumentType]

    elif isinstance(tabs_source, list):
        # Normalized tab definitions (list of dicts with type markers)
        tab_widgets = _set_tabs_from_normalized(host, tab_widget, tabs_source)  # pyright: ignore[reportUnknownArgumentType]

    # Set up selection bindings
    if field_info.tab_selected_index:
        _setup_tab_index_binding(host, tab_widget, field_info.tab_selected_index)
    if field_info.tab_selected_widget:
        _setup_tab_widget_binding(host, tab_widget, field_info.tab_selected_widget)
