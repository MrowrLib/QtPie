"""Model binding logic for QComboBox, QListView, QTreeView, QTableView."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, get_proxies_for, on_proxy_registered
from qtpy.QtWidgets import QWidget

from qtpie.models.reactive_table_model import DICT_KEY_COLUMN

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.models import ReactiveListModel, ReactiveTreeModel


def _resolve_on_edited_callback(
    host: QWidget,
    on_edited_spec: str | Callable[..., Any] | None,
) -> Callable[[Any, Any, Any], None] | None:
    """Resolve the onEdited callback from a string method name or callable.

    Args:
        host: The widget instance to look up method names on.
        on_edited_spec: Either a callable, a method name string, or None.

    Returns:
        A callable (item, old_value, new_value) -> None, or None if not specified.
    """
    if on_edited_spec is None:
        return None

    if callable(on_edited_spec):
        return on_edited_spec  # type: ignore[return-value]

    # It's a string - look up the method on the host
    method = getattr(host, on_edited_spec, None)
    if method is not None and callable(method):
        return method  # type: ignore[return-value]

    return None


def _apply_edit_triggers(
    view: QWidget,
    edit_on_double_click: bool | None,
    edit_on_select: bool | None,
    edit_on_edit_key: bool | None,
) -> None:
    """Apply edit trigger configuration to a QAbstractItemView.

    Args:
        view: The QListView/QTreeView widget
        edit_on_double_click: Enable double-click editing (default: True)
        edit_on_select: Enable click-selected-item editing (default: False)
        edit_on_edit_key: Enable F2/Enter key editing (default: True)
    """
    from qtpy.QtWidgets import QAbstractItemView

    if not isinstance(view, QAbstractItemView):
        return

    # Apply defaults
    if edit_on_double_click is None:
        edit_on_double_click = True
    if edit_on_select is None:
        edit_on_select = False
    if edit_on_edit_key is None:
        edit_on_edit_key = True

    # Build trigger flags
    triggers = QAbstractItemView.EditTrigger.NoEditTriggers
    if edit_on_double_click:
        triggers = triggers | QAbstractItemView.EditTrigger.DoubleClicked
    if edit_on_select:
        triggers = triggers | QAbstractItemView.EditTrigger.SelectedClicked
    if edit_on_edit_key:
        triggers = triggers | QAbstractItemView.EditTrigger.EditKeyPressed

    view.setEditTriggers(triggers)


def _apply_table_header_config(
    view: QWidget,
    column_resize_mode: str | None,
    stretch_last_column: bool | None,
) -> None:
    """Apply QTableView header configuration (columnResizeMode, stretchLastColumn).

    Args:
        view: The QTableView widget
        column_resize_mode: Resize mode string ("interactive", "fixed", "stretch", "resize_to_contents")
                           Defaults to "stretch" (QtPie default) if not specified.
        stretch_last_column: If True/False, explicitly set stretchLastSection.
                            If None, no change from Qt default (unless columnResizeMode is "stretch").
    """
    from qtpy.QtWidgets import QHeaderView, QTableView

    if not isinstance(view, QTableView):
        return

    header = view.horizontalHeader()

    # Map string literals to QHeaderView.ResizeMode enum
    resize_mode_map: dict[str, QHeaderView.ResizeMode] = {
        "interactive": QHeaderView.ResizeMode.Interactive,
        "fixed": QHeaderView.ResizeMode.Fixed,
        "stretch": QHeaderView.ResizeMode.Stretch,
        "resize_to_contents": QHeaderView.ResizeMode.ResizeToContents,
    }

    # Default to "stretch" if not specified (QtPie opinion: tables should fill their space)
    effective_resize_mode = column_resize_mode if column_resize_mode is not None else "stretch"

    if effective_resize_mode in resize_mode_map:
        header.setSectionResizeMode(resize_mode_map[effective_resize_mode])

    # Apply stretchLastColumn if explicitly set
    if stretch_last_column is not None:
        header.setStretchLastSection(stretch_last_column)


def _setup_tree_record_watcher(
    host: QWidget,
    model: ReactiveTreeModel[Any],
    bind_path: str,
    children_attr: str,
) -> None:
    """Watch for host widget's record changes and update tree model source.

    When the host Widget[T]'s record is replaced (e.g., after workspace.refresh()),
    this detects the change and calls replace_source on the tree model so it
    watches the new record's data.

    Args:
        host: The host Widget[T] containing the tree.
        model: The ReactiveTreeModel to update.
        bind_path: The binding path (e.g., "items") to resolve on the record.
        children_attr: Attribute name for accessing children.
    """
    from qtpie.variable import RecordVariable

    # Get host's record variable
    record_var = getattr(host, "record", None)
    if record_var is None or not isinstance(record_var, RecordVariable):
        return

    # Track the last record object id to detect actual replacements
    last_record_id: list[int] = [id(record_var.value) if record_var.value is not None else 0]  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]

    def on_record_change() -> None:
        """Called when host's record value changes."""
        current_record = cast(Any, record_var.value)  # pyright: ignore[reportUnknownMemberType]
        current_id = id(current_record) if current_record is not None else 0

        # Only update if the record object itself changed (not just a property)
        if current_id == last_record_id[0]:
            return
        last_record_id[0] = current_id

        if current_record is None:
            return

        # Re-resolve the binding path on the new record
        # bind_path is something like "items"
        attr = cast(Any, getattr(current_record, bind_path, None))
        if attr is None:
            return

        # Extract ObservableList from the attribute
        new_obs_list: ObservableList[Any] | None = None
        if hasattr(attr, "observable"):
            # It's a Variable - get the underlying Observable
            wrapper: Any = attr.observable
            if isinstance(wrapper, ObservableList):
                new_obs_list = cast(ObservableList[Any], wrapper)
            elif hasattr(wrapper, "get"):
                val: Any = wrapper.get()
                if isinstance(val, ObservableList):
                    new_obs_list = cast(ObservableList[Any], val)
        elif isinstance(attr, ObservableList):
            new_obs_list = cast(ObservableList[Any], attr)

        if new_obs_list is not None:
            model.replace_source(new_obs_list)

    # Subscribe to record changes
    record_var.observable.on_change(on_record_change)  # pyright: ignore[reportUnknownMemberType]


def _setup_tree_proxy_watching(
    model: ReactiveTreeModel[Any],
    obs_list: ObservableList[Any],
    children_attr: str,
) -> None:
    """Set up watching for proxy changes so tree updates when item properties change.

    When items in the tree are edited through ObservableProxy (e.g., in a Widget[T]),
    this ensures the tree model emits dataChanged so the view updates.

    Args:
        model: The ReactiveTreeModel to notify when items change.
        obs_list: The ObservableList backing the model.
        children_attr: Attribute name for accessing children.
    """
    import weakref

    # Track which (item_id, proxy_id) pairs we've subscribed to
    subscribed_pairs: set[tuple[int, int]] = set()

    # Use weak reference to model so callback doesn't prevent GC
    model_ref = weakref.ref(model)

    # Collect all items in the tree (root + nested children)
    def get_all_items() -> set[int]:
        """Get ids of all items currently in the tree."""
        all_ids: set[int] = set()

        def collect(item: Any) -> None:
            all_ids.add(id(item))
            children = getattr(item, children_attr, None)
            if children:
                for child in children:
                    collect(child)

        for item in obs_list:
            collect(item)
        return all_ids

    def subscribe_to_proxy(item: Any, proxy: ObservableProxy[Any]) -> None:
        """Subscribe to a proxy's changes for a specific item."""
        pair_key = (id(item), id(proxy))
        if pair_key in subscribed_pairs:
            return
        subscribed_pairs.add(pair_key)

        # Create a closure that captures the item and weak model ref
        def on_proxy_change() -> None:
            m = model_ref()
            if m is None:
                return  # Model was garbage collected
            # Check if Qt C++ object is still valid using shiboken
            try:
                from shiboken6 import isValid

                if not isValid(m):
                    return  # C++ object deleted
            except ImportError:
                pass  # Not using PySide6, skip check
            try:
                m.notify_item_changed(item)
            except RuntimeError:
                pass  # C++ object deleted during call

        proxy.on_change(on_proxy_change)

    def subscribe_to_item(item: Any) -> None:
        """Subscribe to all existing proxies for an item."""
        for proxy in get_proxies_for(item):
            subscribe_to_proxy(item, proxy)

        # Also subscribe to children recursively
        children = getattr(item, children_attr, None)
        if children:
            for child in children:
                subscribe_to_item(child)

    # Subscribe to all existing items and their existing proxies
    for item in obs_list:
        subscribe_to_item(item)

    # Subscribe to new items when they're added to the list
    def on_insert(_index: int, item: Any) -> None:
        subscribe_to_item(item)

    obs_list.on_insert(on_insert)

    # Register global callback to be notified when NEW proxies are created
    # This handles the case where an item is opened in an editor AFTER the tree is created
    def on_new_proxy(target: Any, proxy: ObservableProxy[Any]) -> None:
        # Check if model still exists
        if model_ref() is None:
            return
        # Check if this target is one of our tree items
        target_id = id(target)
        all_item_ids = get_all_items()
        if target_id in all_item_ids:
            subscribe_to_proxy(target, proxy)

    on_proxy_registered(on_new_proxy)


def _setup_list_proxy_watching(
    model: ReactiveListModel[Any],
    obs_list: ObservableList[Any],
) -> None:
    """Set up watching for proxy changes so list view updates when item properties change.

    When items in the list are edited through ObservableProxy (e.g., in a Widget[T]),
    this ensures the list model emits dataChanged so the view updates.

    Args:
        model: The ReactiveListModel to notify when items change.
        obs_list: The ObservableList backing the model.
    """
    import weakref

    # Track which (item_id, proxy_id) pairs we've subscribed to
    subscribed_pairs: set[tuple[int, int]] = set()

    # Use weak reference to model so callback doesn't prevent GC
    model_ref = weakref.ref(model)

    def get_all_items() -> set[int]:
        """Get ids of all items currently in the list."""
        return {id(item) for item in obs_list}

    def subscribe_to_proxy(item: Any, proxy: ObservableProxy[Any]) -> None:
        """Subscribe to a proxy's changes for a specific item."""
        pair_key = (id(item), id(proxy))
        if pair_key in subscribed_pairs:
            return
        subscribed_pairs.add(pair_key)

        # Create a closure that captures the item and weak model ref
        def on_proxy_change() -> None:
            m = model_ref()
            if m is None:
                return  # Model was garbage collected
            # Check if Qt C++ object is still valid using shiboken
            try:
                from shiboken6 import isValid

                if not isValid(m):
                    return  # C++ object deleted
            except ImportError:
                pass  # Not using PySide6, skip check
            try:
                m.notify_item_changed(item)
            except RuntimeError:
                pass  # C++ object deleted during call

        proxy.on_change(on_proxy_change)

    def subscribe_to_item(item: Any) -> None:
        """Subscribe to all existing proxies for an item."""
        for proxy in get_proxies_for(item):
            subscribe_to_proxy(item, proxy)

    # Subscribe to all existing items and their existing proxies
    for item in obs_list:
        subscribe_to_item(item)

    # Subscribe to new items when they're added to the list
    def on_insert(_index: int, item: Any) -> None:
        subscribe_to_item(item)

    obs_list.on_insert(on_insert)

    # Register global callback to be notified when NEW proxies are created
    def on_new_proxy(target: Any, proxy: ObservableProxy[Any]) -> None:
        # Check if model still exists
        if model_ref() is None:
            return
        # Check if this target is one of our list items
        target_id = id(target)
        all_item_ids = get_all_items()
        if target_id in all_item_ids:
            subscribe_to_proxy(target, proxy)

    on_proxy_registered(on_new_proxy)


def _setup_embedded_widget(
    host: QWidget,
    view: QWidget,
    model: Any,
    obs_list: ObservableList[Any],
    widget_class: type,
    embed_config: Any | None,
    is_tree: bool = False,
) -> None:
    """Set up embedded widgets in QListView or QTreeView using persistent editors.

    Args:
        host: The Widget/Window instance containing the view
        view: The QListView or QTreeView widget
        model: The ReactiveListModel or ReactiveTreeModel
        obs_list: The ObservableList backing the model
        widget_class: The Widget class to embed for each item
        embed_config: Optional EmbedConfig with kwargs (or None for simple case)
        is_tree: Whether this is a QTreeView (enables recursive editor opening)
    """
    from qtpie.delegates import QtPieWidgetDelegate
    from qtpie.embed import EmbedConfig

    # Create the delegate
    config = embed_config if isinstance(embed_config, EmbedConfig) else None
    delegate = QtPieWidgetDelegate(
        widget_class=widget_class,
        parent_widget=host,
        embed_config=config,
        parent=view,
    )

    # Set the delegate on the view
    view.setItemDelegate(delegate)  # type: ignore[attr-defined]

    # Open persistent editors for all existing rows
    def open_editors_for_all() -> None:
        _open_all_persistent_editors(view, model, is_tree=is_tree)

    # Open editors immediately (deferred to let model populate)
    from qtpy.QtCore import QModelIndex, QTimer

    QTimer.singleShot(0, open_editors_for_all)

    # For tree views, use the view model's rowsInserted signal to handle ALL row insertions
    # (including nested children). The ObservableList callbacks only fire for root-level changes.
    # NOTE: We connect to view.model() which may be a proxy - this ensures we get proxy indexes.
    if is_tree:
        # Connect to view model's rowsInserted signal to open persistent editors for new rows at ANY level
        def on_rows_inserted(parent: QModelIndex, first: int, last: int) -> None:
            view_model = view.model()  # type: ignore[attr-defined]
            if view_model is None:
                return
            for row in range(first, last + 1):
                index = view_model.index(row, 0, parent)  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]
                view.openPersistentEditor(index)  # type: ignore[attr-defined]

        # Connect to view.model().rowsInserted - view.model() is the proxy if filter=/sort= is used
        view_model = view.model()  # type: ignore[attr-defined]
        if view_model is not None:
            view_model.rowsInserted.connect(on_rows_inserted)  # pyright: ignore[reportUnknownMemberType]

        # Also handle model reset (e.g., when workspace changes completely)
        def on_model_reset() -> None:
            # Defer to allow model to fully populate
            QTimer.singleShot(0, open_editors_for_all)

        # Handle filter/layout changes - when filter changes, rows may appear/disappear
        # without rowsInserted/rowsRemoved being emitted
        def on_layout_changed(*_: Any) -> None:
            QTimer.singleShot(0, open_editors_for_all)

        if view_model is not None:
            view_model.layoutChanged.connect(on_layout_changed)  # pyright: ignore[reportUnknownMemberType]

        if view_model is not None:
            view_model.modelReset.connect(on_model_reset)  # pyright: ignore[reportUnknownMemberType]
    else:
        # For flat lists, use ObservableList callbacks (simpler, no nesting)
        def on_insert(index: int, _item: Any) -> None:
            model_index = model.index(index, 0)
            view.openPersistentEditor(model_index)  # type: ignore[attr-defined]

        def on_remove(_index: int, _item: Any) -> None:
            # Qt automatically closes the editor when the row is removed
            pass

        def on_replace(index: int, _old: Any, _new: Any) -> None:
            # Close and reopen editor for replaced item
            model_index = model.index(index, 0)
            view.closePersistentEditor(model_index)  # type: ignore[attr-defined]
            view.openPersistentEditor(model_index)  # type: ignore[attr-defined]

        def on_clear(_items: list[Any]) -> None:
            # All editors automatically closed when model is cleared
            pass

        obs_list.on_insert(on_insert)
        obs_list.on_remove(on_remove)
        obs_list.on_replace(on_replace)
        obs_list.on_clear(on_clear)


def _setup_table_widget_columns(
    host: QWidget,
    view: QWidget,
    model: Any,
    obs_list: ObservableList[Any],
    widget_columns: list[tuple[int, type, Any | None]],
) -> None:
    """Set up embedded widgets in specific QTableView columns using persistent editors.

    Args:
        host: The Widget/Window instance containing the view
        view: The QTableView widget
        model: The ReactiveTableModel
        obs_list: The ObservableList backing the model
        widget_columns: List of (column_index, widget_class, embed_config) tuples
    """
    from qtpie.delegates import QtPieWidgetDelegate
    from qtpie.embed import EmbedConfig

    # Create a delegate for each widget column
    for col_index, widget_class, embed_config in widget_columns:
        config = embed_config if isinstance(embed_config, EmbedConfig) else None
        delegate = QtPieWidgetDelegate(
            widget_class=widget_class,
            parent_widget=host,
            embed_config=config,
            parent=view,
        )

        # Set delegate for this specific column
        view.setItemDelegateForColumn(col_index, delegate)  # type: ignore[attr-defined]

    # Open persistent editors for all existing rows in widget columns
    def open_editors_for_all() -> None:
        for row in range(model.rowCount()):
            for col_index, _widget_class, _embed_config in widget_columns:
                model_index = model.index(row, col_index)
                view.openPersistentEditor(model_index)  # type: ignore[attr-defined]

    # Open editors immediately (deferred to let model populate)
    from qtpy.QtCore import QTimer

    QTimer.singleShot(0, open_editors_for_all)

    # Subscribe to list changes to manage persistent editors
    def on_insert(index: int, _item: Any) -> None:
        # Open persistent editors for all widget columns in the new row
        for col_index, _widget_class, _embed_config in widget_columns:
            model_index = model.index(index, col_index)
            view.openPersistentEditor(model_index)  # type: ignore[attr-defined]

    def on_remove(_index: int, _item: Any) -> None:
        # Qt automatically closes editors when the row is removed
        pass

    def on_replace(index: int, _old: Any, _new: Any) -> None:
        # Close and reopen editors for replaced item
        for col_index, _widget_class, _embed_config in widget_columns:
            model_index = model.index(index, col_index)
            view.closePersistentEditor(model_index)  # type: ignore[attr-defined]
            view.openPersistentEditor(model_index)  # type: ignore[attr-defined]

    def on_clear(_items: list[Any]) -> None:
        # All editors automatically closed when model is cleared
        pass

    obs_list.on_insert(on_insert)
    obs_list.on_remove(on_remove)
    obs_list.on_replace(on_replace)
    obs_list.on_clear(on_clear)


def _open_all_persistent_editors(view: QWidget, model: Any, parent_index: Any = None, is_tree: bool = False) -> None:
    """Recursively open persistent editors for all rows in a view.

    For QTreeView, this traverses the entire tree structure.
    For QListView/QTableView, this opens editors for all rows.

    IMPORTANT: Uses view.model() to get the actual model set on the view,
    which may be a proxy model (when filter= or sort= is used). This ensures
    openPersistentEditor receives correct indexes.

    Args:
        view: The view widget
        model: The source model (unused, kept for API compatibility)
        parent_index: The parent index for tree models (None for root)
        is_tree: Whether this is a tree model (enables recursion)
    """
    from qtpy.QtCore import QModelIndex

    if parent_index is None:
        parent_index = QModelIndex()

    # Use view.model() to get the actual model (could be proxy if filter=/sort= is used)
    view_model = view.model()  # type: ignore[attr-defined]
    if view_model is None:
        return

    row_count = view_model.rowCount(parent_index)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
    for row in range(cast(int, row_count)):
        index = view_model.index(row, 0, parent_index)  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]
        view.openPersistentEditor(index)  # type: ignore[attr-defined]

        # For tree models, recurse into children
        if is_tree and view_model.rowCount(index) > 0:  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
            _open_all_persistent_editors(view, model, index, is_tree=True)

    # Schedule layout recalculation to pick up widget size hints (only at root level)
    if parent_index is not None and not parent_index.isValid() and hasattr(view, "scheduleDelayedItemsLayout"):
        view.scheduleDelayedItemsLayout()  # type: ignore[attr-defined]


def _is_list_view(widget: QWidget) -> bool:
    """Check if widget is a QListView (but not QTableView or QTreeView)."""
    from qtpy.QtWidgets import QListView, QTableView, QTreeView

    return isinstance(widget, QListView) and not isinstance(widget, (QTableView, QTreeView))


def apply_model_binding(
    host: QWidget,
    widget_instance: QWidget,
    source: Any,  # BindingSource
    bind_path: str,
    field_info: Any,  # NewField
    *,
    is_table_view_fn: Callable[[QWidget], bool],
    is_tree_view_fn: Callable[[QWidget], bool],
    resolve_or_create_variable_fn: Callable[[QWidget, str, type | None], Any],
) -> bool:
    """Apply model binding for QComboBox, QListView, QTreeView, QTableView.

    Returns True if model binding was applied, False otherwise.
    """
    from qtpie.bindings.selection_list import setup_selection_bindings
    from qtpie.bindings.selection_table import setup_table_selection_bindings
    from qtpie.bindings.selection_tree import setup_tree_selection_bindings
    from qtpie.variable import Variable as VarType

    obs_list: ObservableList[Any] | None = None
    root_variable: VarType[Any] | None = None

    # For nested paths like "workspace.collections", find the ROOT Variable
    # so we can re-sync when it changes from None to a real object
    bind_path_normalized = bind_path.replace("?.", ".")
    if "." in bind_path_normalized:
        root_name = bind_path_normalized.split(".")[0]
        # Try to find root variable on host or in parent hierarchy
        # Check both root_name and _root_name (underscore prefix variant)
        root_attr: Any = getattr(host, root_name, None)
        if root_attr is None:
            root_attr = getattr(host, f"_{root_name}", None)
        if root_attr is None:
            # Walk up parent hierarchy
            from qtpy.QtWidgets import QApplication

            current: Any = host
            while root_attr is None:
                if not hasattr(current, "parent") or not callable(current.parent):
                    break
                parent: Any = current.parent()
                if parent is None:
                    break
                root_attr = getattr(parent, root_name, None)
                current = parent
            # Fallback to QApplication
            if root_attr is None:
                app = QApplication.instance()
                if app is not None:
                    root_attr = getattr(app, root_name, None)
        if root_attr is not None and isinstance(root_attr, VarType):
            root_variable = cast(VarType[Any], root_attr)

    # Extract ObservableList from Variable or use directly
    # Also handle dict -> list[KeyValuePair] conversion for QTableView
    is_dict_binding = False
    source_dict: ObservableDict[Any, Any] | dict[Any, Any] | None = None  # Track source dict for editing
    dict_sync: Any = None  # DictToTupleListSync for synced dict bindings

    if isinstance(source, VarType):
        wrapper = source.observable  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if isinstance(wrapper, ObservableList):
            obs_list = wrapper  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(wrapper, ObservableDict):
            # Variable[dict] wraps ObservableDict - use DictToTupleListSync for sync
            from qtpie.models import DictToTupleListSync

            dict_sync = DictToTupleListSync(cast(ObservableDict[Any, Any], wrapper))
            obs_list = dict_sync.list
            source_dict = cast(ObservableDict[Any, Any], wrapper)
            is_dict_binding = True
        elif isinstance(wrapper, (Observable, ObservableProxy)):
            # Source might be Observable[list] or ObservableProxy with nested list
            # Create a synced ObservableList that updates when source changes
            val = wrapper.get() if isinstance(wrapper, Observable) else wrapper.unwrap()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(val, ObservableList):
                # Already an ObservableList - use it directly!
                obs_list = val  # pyright: ignore[reportUnknownVariableType]
            elif isinstance(val, list):
                obs_list = ObservableList(cast(list[Any], val))
            elif isinstance(val, dict):
                # Plain dict - no sync, just snapshot
                obs_list = ObservableList(list(cast(dict[Any, Any], val).items()))
                source_dict = cast(dict[Any, Any], val)  # Track for editing
                is_dict_binding = True
            elif val is None:
                # Initially None - create empty list, will populate later
                obs_list = ObservableList[Any]()
    elif isinstance(source, ObservableList):
        obs_list = source  # pyright: ignore[reportUnknownVariableType]
    elif isinstance(source, ObservableDict):
        # ObservableDict directly - use DictToTupleListSync for sync
        from qtpie.models import DictToTupleListSync

        dict_sync = DictToTupleListSync(cast(ObservableDict[Any, Any], source))
        obs_list = dict_sync.list
        source_dict = cast(ObservableDict[Any, Any], source)
        is_dict_binding = True
    elif isinstance(source, Observable):
        val = source.get()  # pyright: ignore[reportUnknownVariableType]
        if isinstance(val, ObservableList):
            # Already an ObservableList - use it directly!
            obs_list = val  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(val, list):
            obs_list = ObservableList(cast(list[Any], val))
        elif isinstance(val, dict):
            # Plain dict - no sync, just snapshot
            obs_list = ObservableList(list(cast(dict[Any, Any], val).items()))
            source_dict = cast(dict[Any, Any], val)  # Track for editing
            is_dict_binding = True
        elif val is None:
            obs_list = ObservableList[Any]()

    if obs_list is None:
        return False

    # Decide which model type to use
    # QTableView (or explicit columns=) uses ReactiveTableModel
    # QTreeView (or explicit children=) uses ReactiveTreeModel
    # Others (QComboBox, QListView) use ReactiveListModel
    use_table_model = is_table_view_fn(widget_instance) or field_info.table_columns is not None
    use_tree_model = is_tree_view_fn(widget_instance) or field_info.tree_children is not None

    if use_tree_model:
        # Create ReactiveTreeModel for QTreeView
        from qtpie.bindings.format_binding import create_item_formatter
        from qtpie.models import ReactiveTreeModel

        # Check for format= to customize item display
        # Can be string template "{name}" or callable (lambda, dict.get)
        format_fn: Callable[[Any], str] | None = None
        if field_info.model_format is not None:
            if callable(field_info.model_format):
                format_fn = cast("Callable[[Any], str]", field_info.model_format)
            else:
                format_fn = create_item_formatter(field_info.model_format)

        # Default children attribute to "children" if not specified
        children_attr = field_info.tree_children or "children"

        # Resolve onEdited callback
        on_edited_callback = _resolve_on_edited_callback(host, field_info.tree_on_edited)

        model = ReactiveTreeModel(
            obs_list,
            parent=widget_instance,
            children_attr=children_attr,
            format_fn=format_fn,
            checkable=field_info.tree_checkable,
            editable=field_info.tree_editable,
            on_edited=on_edited_callback,
        )

        # Watch for host widget's record changes and update tree model source
        # This handles cases where the record itself is replaced (e.g., workspace.refresh())
        _setup_tree_record_watcher(host, model, bind_path, children_attr)

        # Set edit triggers if editable is enabled
        if field_info.tree_editable is not None and field_info.tree_editable is not False:
            _apply_edit_triggers(
                widget_instance,
                field_info.edit_on_double_click,
                field_info.edit_on_select,
                field_info.edit_on_edit_key,
            )

            # Apply validator delegate if validator= is specified
            if field_info.tree_validator is not None:
                from qtpie.delegates import ValidatorItemDelegate

                validator_delegate = ValidatorItemDelegate(field_info.tree_validator, parent=widget_instance)
                widget_instance.setItemDelegate(validator_delegate)  # type: ignore[attr-defined]
    elif use_table_model:
        # Create ReactiveTableModel for QTableView
        from qtpie.models import ReactiveTableModel

        # For dict bindings, use tuple index columns if not specified
        columns = field_info.table_columns
        columns_were_explicit = columns is not None
        headers = field_info.table_headers

        # Detect dict binding from columns if #key is present
        # This handles the case where the initial value is None but we know it's a dict
        if columns is not None and DICT_KEY_COLUMN in columns:
            is_dict_binding = True
            # Create dict_sync if not already created (initial value was None)
            if dict_sync is None:
                from qtpie.models import DictToTupleListSync

                # Create empty sync adapter - will be populated via replace_source later
                dict_sync = DictToTupleListSync(cast(dict[Any, Any], {}))
                # Use the dict_sync's list as our obs_list
                obs_list = dict_sync.list

        # At this point obs_list must be set (or we would have returned False earlier)
        assert obs_list is not None

        # For dict bindings without explicit columns, let ReactiveTableModel auto-detect
        # It will use #key + value properties if value is a complex object,
        # or [0, 1] for simple dict[K, V] where V is primitive.
        # Don't pre-set headers here - let _auto_detect_columns() set appropriate headers
        # based on what columns it detects.

        # Resolve editable - default is True (like other Qt widgets)
        # readOnly=True sets editable=False
        editable = field_info.table_editable
        if field_info.table_readonly is True:
            editable = False
        elif editable is None:
            # Default: editable=True (consistent with QLineEdit, QTextEdit, etc.)
            editable = True

        # For dict bindings, map "key"/"value" to column indices or #key
        # Only map when using default columns (columns not explicitly specified)
        if is_dict_binding and isinstance(editable, list) and not columns_were_explicit:
            mapped_editable: list[str | int] = []
            for col in cast(list[str | int], editable):
                if col == "key":
                    # Map "key" to "#key" for new-style dict bindings
                    mapped_editable.append("#key")
                elif col == "value":
                    mapped_editable.append(1)
                else:
                    mapped_editable.append(col)
            editable = mapped_editable

        model = ReactiveTableModel(
            obs_list,
            parent=widget_instance,
            columns=columns,
            prepend_columns=field_info.table_prepend_columns,
            append_columns=field_info.table_append_columns,
            headers=headers,
            checkable=field_info.table_checkable,
            checkable_text=field_info.table_checkable_text,
            editable=cast("list[str | int] | bool | None", editable),
            source_dict=source_dict,
            dict_sync=dict_sync,
            key_header=field_info.key_header,
            value_header=field_info.value_header,
        )
    else:
        # Create ReactiveListModel for QComboBox, QListView, etc.
        from qtpie.bindings.format_binding import create_item_formatter
        from qtpie.models import ReactiveListModel

        # Check for format= to customize item display
        # Can be string template "{name}" or callable (lambda, dict.get)
        format_fn = None
        if field_info.model_format is not None:
            if callable(field_info.model_format):
                format_fn = cast("Callable[[Any], str]", field_info.model_format)
            else:
                format_fn = create_item_formatter(field_info.model_format)

        # Resolve onEdited callback
        on_edited_callback = _resolve_on_edited_callback(host, field_info.list_on_edited)

        model = ReactiveListModel(
            obs_list,
            parent=widget_instance,
            format_fn=format_fn,
            checkable=field_info.list_checkable,
            editable=field_info.list_editable,
            on_edited=on_edited_callback,
        )

        # Set edit triggers if editable is enabled (for QListView only, not QComboBox)
        if field_info.list_editable is not None and field_info.list_editable is not False:
            _apply_edit_triggers(
                widget_instance,
                field_info.edit_on_double_click,
                field_info.edit_on_select,
                field_info.edit_on_edit_key,
            )

            # Apply validator delegate if validator= is specified
            if field_info.list_validator is not None:
                from qtpie.delegates import ValidatorItemDelegate

                validator_delegate = ValidatorItemDelegate(field_info.list_validator, parent=widget_instance)
                widget_instance.setItemDelegate(validator_delegate)  # type: ignore[attr-defined]

    # Wrap in filter/sort proxy if filter= or sort= is specified
    if field_info.model_filter is not None or field_info.model_sort is not None:
        from qtpie.models import ReactiveFilterProxyModel

        proxy = ReactiveFilterProxyModel(
            parent=widget_instance,
            filter_expr=field_info.model_filter,
            filter_depends=field_info.filter_depends,
            sort_key=field_info.model_sort,
            widget=host,  # type: ignore[arg-type]
        )
        proxy.setSourceModel(model)
        widget_instance.setModel(proxy)  # type: ignore[attr-defined]
    else:
        widget_instance.setModel(model)  # type: ignore[attr-defined]

    # Apply QTableView header configuration (columnResizeMode, stretchLastColumn)
    if use_table_model and is_table_view_fn(widget_instance):
        _apply_table_header_config(
            widget_instance,
            column_resize_mode=field_info.table_column_resize_mode,
            stretch_last_column=field_info.table_stretch_last_column,
        )

    # For nested paths, subscribe to ROOT Variable to re-sync when it changes
    # Also handle expand=True for QTreeView
    should_expand = use_tree_model and getattr(field_info, "tree_expand", False)

    # Only set up root sync if we COPIED the list (obs_list is not the source).
    # If source is already an ObservableList, the model uses it directly - no sync needed.
    needs_root_sync = root_variable is not None and not isinstance(source, ObservableList)
    if needs_root_sync:
        nested_path = ".".join(bind_path_normalized.split(".")[1:])

        def make_root_sync_for_model(
            root_var: VarType[Any],
            target: ObservableList[Any],
            path: str,
            tree_widget: QWidget | None,
            expand_on_change: bool,
            dict_sync_adapter: Any = None,  # DictToTupleListSync for dict bindings
        ) -> None:
            # Track the last nested list identity to detect when the root object changes
            # vs when the same list is just mutated. We only want to re-sync when the
            # actual list object changes (e.g., record replaced), not on every mutation.
            # Use a list for mutable closure capture.
            last_nested_list_id: list[int] = [-1]  # -1 = not initialized yet
            syncing = False  # Re-entrancy guard

            # Track subscribed ObservableLists to avoid duplicate subscriptions
            subscribed_lists: set[int] = set()

            def subscribe_to_nested_list(nested_list: ObservableList[Any]) -> None:
                """Subscribe to nested ObservableList changes to keep target in sync."""
                list_id = id(nested_list)
                if list_id in subscribed_lists:
                    return
                subscribed_lists.add(list_id)

                def on_nested_insert(index: int, item: Any) -> None:
                    nonlocal syncing
                    if syncing:
                        return
                    syncing = True
                    try:
                        target.insert(index, item)
                    finally:
                        syncing = False

                def on_nested_remove(index: int, _item: Any) -> None:
                    nonlocal syncing
                    if syncing:
                        return
                    syncing = True
                    try:
                        target.pop(index)
                    finally:
                        syncing = False

                def on_nested_replace(index: int, _old: Any, new: Any) -> None:
                    nonlocal syncing
                    if syncing:
                        return
                    syncing = True
                    try:
                        target[index] = new
                    finally:
                        syncing = False

                def on_nested_clear(_items: list[Any]) -> None:
                    nonlocal syncing
                    if syncing:
                        return
                    syncing = True
                    try:
                        target.clear()
                    finally:
                        syncing = False

                nested_list.on_insert(on_nested_insert)
                nested_list.on_remove(on_nested_remove)
                nested_list.on_replace(on_nested_replace)
                nested_list.on_clear(on_nested_clear)

            def on_root_change(*_: Any) -> None:
                nonlocal syncing
                if syncing:
                    return

                root_val: Any = root_var.value
                if root_val is None:
                    if last_nested_list_id[0] != 0:
                        syncing = True
                        try:
                            target.clear()
                        finally:
                            syncing = False
                        last_nested_list_id[0] = 0
                    return

                # Traverse nested path, unwrapping Variables at each step
                # Track the final Variable we end on (if any) to get its ObservableDict wrapper
                nested_val: Any = root_val
                final_variable: Any = None  # Track Variable[dict] for ObservableDict access
                for part in path.split("."):
                    if nested_val is None:
                        break
                    # Unwrap Variable to get its value before traversing
                    if hasattr(nested_val, "value") and hasattr(nested_val, "observable"):
                        # It's a Variable-like object
                        nested_val = nested_val.value
                        if nested_val is None:
                            break
                    attr_val = getattr(nested_val, part, None)
                    # Check if we landed on a Variable (needed for dict sync)
                    if hasattr(attr_val, "value") and hasattr(attr_val, "observable"):
                        final_variable = attr_val
                    nested_val = attr_val

                # Final unwrap: if we ended on a Variable[list/dict], get the value
                if nested_val is not None and hasattr(nested_val, "value") and hasattr(nested_val, "observable"):
                    final_variable = nested_val
                    nested_val = nested_val.value

                # Only re-sync if the nested list/dict object itself changed (identity change)
                # Skip if it's the same collection just being mutated - this prevents expensive
                # clear()+extend() on every append/remove to the nested list
                if isinstance(nested_val, (list, ObservableList)):
                    nested_id = id(cast(list[Any], nested_val))
                    if nested_id != last_nested_list_id[0]:
                        last_nested_list_id[0] = nested_id
                        syncing = True
                        try:
                            target.clear()
                            target.extend(cast(list[Any], nested_val))
                        finally:
                            syncing = False

                        # Subscribe to the nested ObservableList so future changes sync
                        if isinstance(nested_val, ObservableList):
                            subscribe_to_nested_list(cast(ObservableList[Any], nested_val))

                        # Expand all if requested (QTreeView with expand=True)
                        # This fires when data is loaded/replaced (e.g., new workspace)
                        if expand_on_change and tree_widget is not None:
                            from qtpy.QtCore import QTimer

                            # Defer expandAll to after model updates
                            QTimer.singleShot(0, tree_widget.expandAll)  # type: ignore[attr-defined]
                elif isinstance(nested_val, (dict, ObservableDict)):
                    # Handle dict -> list[(key, value)] conversion for QTableView
                    nested_dict = cast(dict[Any, Any], nested_val)
                    nested_id = id(nested_dict)
                    if nested_id != last_nested_list_id[0]:
                        last_nested_list_id[0] = nested_id
                        syncing = True
                        try:
                            # If we have a dict_sync adapter, use replace_source to update it
                            # This keeps the sync adapter connected to the new source dict
                            if dict_sync_adapter is not None and final_variable is not None:
                                # Get the ObservableDict wrapper from the Variable
                                new_obs_dict = final_variable.observable
                                if isinstance(new_obs_dict, ObservableDict):
                                    dict_sync_adapter.replace_source(new_obs_dict)
                                else:
                                    # Fallback for plain dict
                                    target.clear()
                                    target.extend(list(cast(dict[Any, Any], nested_val).items()))
                            else:
                                target.clear()
                                # Convert dict to list of (key, value) tuples
                                target.extend(list(cast(dict[Any, Any], nested_val).items()))
                        finally:
                            syncing = False
                elif nested_val is None and last_nested_list_id[0] != 0:
                    syncing = True
                    try:
                        target.clear()
                    finally:
                        syncing = False
                    last_nested_list_id[0] = 0

            # Subscribe to root variable
            root_var.observable.on_change(on_root_change)  # pyright: ignore[reportUnknownMemberType]

            # Also subscribe to any intermediate Variables along the path
            # e.g., for "active_environment.variables", subscribe to active_environment
            def subscribe_to_intermediate_variables() -> None:
                """Traverse path and subscribe to all Variables along the way."""
                current_value: Any = root_var.value
                subscribed_ids: set[int] = {id(root_var.observable)}  # type: ignore[arg-type]

                for part in path.split(".")[:-1]:  # Skip the final part (target)
                    if current_value is None:
                        break
                    nested_attr: Any = getattr(current_value, part, None)
                    if nested_attr is not None and hasattr(nested_attr, "observable"):
                        # It's a Variable - subscribe to it
                        obs = nested_attr.observable
                        obs_id = id(obs)
                        if obs_id not in subscribed_ids:
                            obs.on_change(on_root_change)  # pyright: ignore[reportUnknownMemberType]
                            subscribed_ids.add(obs_id)
                        current_value = nested_attr.value
                    else:
                        current_value = nested_attr

            subscribe_to_intermediate_variables()

        assert root_variable is not None  # Checked in needs_root_sync condition
        make_root_sync_for_model(
            root_variable,
            obs_list,
            nested_path,
            widget_instance if should_expand else None,
            should_expand,
            dict_sync_adapter=dict_sync if is_dict_binding else None,
        )

    # Set up selection bindings based on widget type
    deselect_on_escape = getattr(field_info, "deselect_on_escape", True)
    if use_tree_model:
        # QTreeView selection bindings
        setup_tree_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_item,
            field_info.selected_items,
            field_info.selected_widget,
            resolve_or_create_variable_fn=resolve_or_create_variable_fn,
            root_variable=root_variable,  # Pass root for nested path subscriptions
            deselect_on_escape=deselect_on_escape,
        )

        # Handle expand=True: expandAll immediately and on data changes
        if should_expand:
            from qtpy.QtCore import QTimer

            # Expand all immediately after model is set (defer to let model populate)
            QTimer.singleShot(0, widget_instance.expandAll)  # type: ignore[attr-defined]

        # Handle headerHidden= (default: True)
        header_hidden = getattr(field_info, "tree_header_hidden", True)
        widget_instance.setHeaderHidden(header_hidden)  # type: ignore[attr-defined]

        # Set up proxy watching for format= bindings so tree updates when item properties change
        if field_info.model_format is not None and not callable(field_info.model_format):
            from qtpie.models import ReactiveTreeModel

            _setup_tree_proxy_watching(cast("ReactiveTreeModel[Any]", model), obs_list, field_info.tree_children or "children")

    elif use_table_model:
        # QTableView-specific selection bindings
        setup_table_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_row,
            field_info.selected_column,
            field_info.selected_cell,
            field_info.selected_item,
            field_info.selected_rows,
            field_info.selected_columns,
            field_info.selected_cells,
            field_info.selected_items,
            field_info.selected_widget,
            resolve_or_create_variable_fn=resolve_or_create_variable_fn,
            root_variable=root_variable,  # Pass root for nested path subscriptions
            deselect_on_escape=deselect_on_escape,
        )
        # Set up embedded widgets for QTableView columns
        # Merge widget columns from main columns=, prependColumns=, and appendColumns=
        all_widget_columns: list[tuple[int, type, Any | None]] = []

        # Prepend widget columns (indices are already correct, start from 0)
        if field_info.table_prepend_widget_columns:
            all_widget_columns.extend(field_info.table_prepend_widget_columns)

        # Main columns= widget columns (offset by prepend length)
        if field_info.table_widget_columns:
            prepend_offset = len(field_info.table_prepend_columns or [])
            for col_idx, widget_cls, embed_cfg in field_info.table_widget_columns:
                all_widget_columns.append((col_idx + prepend_offset, widget_cls, embed_cfg))

        # Append widget columns (offset = total columns - append columns length)
        # NOTE: If model needs to re-detect columns (empty list), we must defer this
        # until columns are known. We'll handle this after checking _needs_redetect_from_items.
        append_widget_columns = field_info.table_append_widget_columns

        # Check if model needs column re-detection (empty list with prepend/append)
        needs_redetect = getattr(model, "_needs_redetect_from_items", False)

        if append_widget_columns and not needs_redetect:
            # Columns are already known - calculate offset now
            total_cols = len(model._columns)  # type: ignore[attr-defined]
            append_len = len(field_info.table_append_columns or [])
            append_offset = total_cols - append_len
            for col_idx, widget_cls, embed_cfg in append_widget_columns:
                all_widget_columns.append((col_idx + append_offset, widget_cls, embed_cfg))

        if all_widget_columns and not needs_redetect:
            _setup_table_widget_columns(host, widget_instance, model, obs_list, all_widget_columns)
        elif needs_redetect:
            # Defer widget column setup until columns are detected
            # Connect to modelReset which fires when columns are re-detected
            def setup_deferred_widget_columns() -> None:
                # Disconnect after first call - we only need to set up once
                model.modelReset.disconnect(setup_deferred_widget_columns)

                # Now calculate correct column indices
                deferred_widget_columns: list[tuple[int, type, Any | None]] = []

                # Prepend columns (indices are correct, start from 0)
                if field_info.table_prepend_widget_columns:
                    deferred_widget_columns.extend(field_info.table_prepend_widget_columns)

                # Main columns= widget columns (offset by prepend length)
                if field_info.table_widget_columns:
                    prepend_off = len(field_info.table_prepend_columns or [])
                    for c_idx, w_cls, e_cfg in field_info.table_widget_columns:
                        deferred_widget_columns.append((c_idx + prepend_off, w_cls, e_cfg))

                # Append widget columns (now columns are known)
                if append_widget_columns:
                    total = len(model._columns)  # type: ignore[attr-defined]
                    append_len = len(field_info.table_append_columns or [])
                    append_off = total - append_len
                    for c_idx, w_cls, e_cfg in append_widget_columns:
                        deferred_widget_columns.append((c_idx + append_off, w_cls, e_cfg))

                if deferred_widget_columns:
                    _setup_table_widget_columns(host, widget_instance, model, obs_list, deferred_widget_columns)

            model.modelReset.connect(setup_deferred_widget_columns)
    else:
        # QComboBox/QListView selection bindings
        # Only enable deselect_on_escape for QListView, not QComboBox
        list_deselect_on_escape = deselect_on_escape and _is_list_view(widget_instance)
        setup_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_index,
            field_info.selected_item,
            field_info.selected_indexes,
            field_info.selected_items_list,
            field_info.selected_widget,
            field_info.selected_text,
            resolve_or_create_variable_fn=resolve_or_create_variable_fn,
            root_variable=root_variable,  # Pass root for nested path subscriptions
            deselect_on_escape=list_deselect_on_escape,
        )
        # Set up embedded widget for QListView (not QComboBox)
        if field_info.embed_widget is not None and _is_list_view(widget_instance):
            _setup_embedded_widget(host, widget_instance, model, obs_list, field_info.embed_widget, field_info.embed_config)

        # Set up proxy watching for format= bindings so list updates when item properties change
        if field_info.model_format is not None and not callable(field_info.model_format):
            from qtpie.models import ReactiveListModel

            _setup_list_proxy_watching(cast("ReactiveListModel[Any]", model), obs_list)

    # Set up embedded widget for QTreeView
    if use_tree_model and field_info.embed_widget is not None:
        _setup_embedded_widget(host, widget_instance, model, obs_list, field_info.embed_widget, field_info.embed_config, is_tree=True)

    return True
