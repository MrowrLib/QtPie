"""Model binding logic for QComboBox, QListView, QTreeView, QTableView."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, get_proxies_for, on_proxy_registered
from qtpy.QtWidgets import QWidget

logger = logging.getLogger("qtpie.bindings")

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.models import ReactiveListModel, ReactiveTreeModel


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
            logger.debug("Proxy changed for %s, notifying tree model", type(item).__name__)
            try:
                m.notify_item_changed(item)
            except RuntimeError:
                pass  # C++ object deleted during call

        proxy.on_change(on_proxy_change)
        logger.debug("Subscribed tree model to proxy changes for %s", type(item).__name__)

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
            logger.debug("New proxy registered for tree item %s, subscribing", type(target).__name__)
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
            logger.debug("Proxy changed for %s, notifying list model", type(item).__name__)
            try:
                m.notify_item_changed(item)
            except RuntimeError:
                pass  # C++ object deleted during call

        proxy.on_change(on_proxy_change)
        logger.debug("Subscribed list model to proxy changes for %s", type(item).__name__)

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
            logger.debug("New proxy registered for list item %s, subscribing", type(target).__name__)
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
    from qtpy.QtCore import QTimer

    QTimer.singleShot(0, open_editors_for_all)

    # Subscribe to list changes to manage persistent editors
    def on_insert(index: int, _item: Any) -> None:
        # Open persistent editor for the new row
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

    Args:
        view: The view widget
        model: The model
        parent_index: The parent index for tree models (None for root)
        is_tree: Whether this is a tree model (enables recursion)
    """
    from qtpy.QtCore import QModelIndex

    if parent_index is None:
        parent_index = QModelIndex()

    row_count = model.rowCount(parent_index)
    for row in range(row_count):
        index = model.index(row, 0, parent_index)
        view.openPersistentEditor(index)  # type: ignore[attr-defined]

        # For tree models, recurse into children
        if is_tree and model.rowCount(index) > 0:
            _open_all_persistent_editors(view, model, index, is_tree=True)


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

    logger.debug(
        "apply_model_binding: source=%s (type=%s), bind_path=%r, widget=%s",
        source,
        type(source).__name__,
        bind_path,
        type(widget_instance).__name__,
    )

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

    if isinstance(source, VarType):
        wrapper = source.observable  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if isinstance(wrapper, ObservableList):
            obs_list = wrapper  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(wrapper, ObservableDict):
            # Variable[dict] wraps ObservableDict - convert to list of tuples
            obs_list = ObservableList(list(cast(ObservableDict[Any, Any], wrapper).items()))
            source_dict = cast(ObservableDict[Any, Any], wrapper)  # Track for editing
            is_dict_binding = True
        elif isinstance(wrapper, (Observable, ObservableProxy)):
            # Source might be Observable[list] or ObservableProxy with nested list
            # Create a synced ObservableList that updates when source changes
            val = wrapper.get() if isinstance(wrapper, Observable) else wrapper.unwrap()  # pyright: ignore[reportUnknownVariableType]
            logger.debug(
                "apply_model_binding: unwrapped val=%s (type=%s), wrapper=%s",
                val,  # pyright: ignore[reportUnknownArgumentType]
                type(val).__name__ if val is not None else None,  # pyright: ignore[reportUnknownArgumentType]
                type(wrapper).__name__,  # pyright: ignore[reportUnknownArgumentType]
            )
            if isinstance(val, ObservableList):
                # Already an ObservableList - use it directly!
                obs_list = val  # pyright: ignore[reportUnknownVariableType]
            elif isinstance(val, list):
                obs_list = ObservableList(cast(list[Any], val))
            elif isinstance(val, dict):
                # Convert dict to list of (key, value) tuples for table display
                obs_list = ObservableList(list(cast(dict[Any, Any], val).items()))
                source_dict = cast(dict[Any, Any], val)  # Track for editing
                is_dict_binding = True
            elif val is None:
                # Initially None - create empty list, will populate later
                obs_list = ObservableList[Any]()
    elif isinstance(source, ObservableList):
        obs_list = source  # pyright: ignore[reportUnknownVariableType]
    elif isinstance(source, ObservableDict):
        # ObservableDict directly - convert to list of tuples
        obs_list = ObservableList(list(cast(ObservableDict[Any, Any], source).items()))
        source_dict = cast(ObservableDict[Any, Any], source)  # Track for editing
        is_dict_binding = True
    elif isinstance(source, Observable):
        val = source.get()  # pyright: ignore[reportUnknownVariableType]
        if isinstance(val, ObservableList):
            # Already an ObservableList - use it directly!
            obs_list = val  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(val, list):
            obs_list = ObservableList(cast(list[Any], val))
        elif isinstance(val, dict):
            obs_list = ObservableList(list(cast(dict[Any, Any], val).items()))
            source_dict = cast(dict[Any, Any], val)  # Track for editing
            is_dict_binding = True
        elif val is None:
            obs_list = ObservableList[Any]()

    if obs_list is None:
        return False

    logger.debug(
        "Model binding: widget=%s, bind_path=%s, list_size=%d, is_source_obs_list=%s",
        type(widget_instance).__name__,
        bind_path,
        len(obs_list),
        isinstance(source, ObservableList),
    )

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

        model = ReactiveTreeModel(
            obs_list,
            parent=widget_instance,
            children_attr=children_attr,
            format_fn=format_fn,
            checkable=field_info.tree_checkable,
            editable=field_info.tree_editable,
        )

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
        headers = field_info.table_headers
        if is_dict_binding and columns is None:
            # Dict items are (key, value) tuples - use index access
            columns = [0, 1]
            if headers is None:
                headers = cast(dict[str | int, str], {0: "Key", 1: "Value"})

        # Resolve editable - default is True (like other Qt widgets)
        # readOnly=True sets editable=False
        editable = field_info.table_editable
        if field_info.table_readonly is True:
            editable = False
        elif editable is None:
            # Default: editable=True (consistent with QLineEdit, QTextEdit, etc.)
            editable = True

        # For dict bindings, map "key"/"value" to column indices
        if is_dict_binding and isinstance(editable, list):
            mapped_editable: list[str | int] = []
            for col in cast(list[str | int], editable):
                if col == "key":
                    mapped_editable.append(0)
                elif col == "value":
                    mapped_editable.append(1)
                else:
                    mapped_editable.append(col)
            editable = mapped_editable

        model = ReactiveTableModel(
            obs_list,
            parent=widget_instance,
            columns=columns,
            headers=headers,
            checkable=field_info.table_checkable,
            checkable_text=field_info.table_checkable_text,
            editable=editable,
            source_dict=source_dict,
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

        model = ReactiveListModel(
            obs_list,
            parent=widget_instance,
            format_fn=format_fn,
            checkable=field_info.list_checkable,
            editable=field_info.list_editable,
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
                logger.debug("Subscribed target to nested ObservableList changes for path=%s", path)

            def on_root_change(*_: Any) -> None:
                nonlocal syncing
                if syncing:
                    logger.debug("on_root_change: skipped (syncing=True) for path=%s", path)
                    return

                logger.debug("on_root_change: triggered for path=%s", path)
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

                # Traverse nested path
                nested_val: Any = root_val
                for part in path.split("."):
                    if nested_val is None:
                        break
                    nested_val = getattr(nested_val, part, None)

                # Only re-sync if the nested list/dict object itself changed (identity change)
                # Skip if it's the same collection just being mutated - this prevents expensive
                # clear()+extend() on every append/remove to the nested list
                if isinstance(nested_val, (list, ObservableList)):
                    nested_id = id(cast(list[Any], nested_val))
                    if nested_id != last_nested_list_id[0]:
                        logger.debug(
                            "on_root_change: list identity changed for path=%s (old_id=%d, new_id=%d), syncing %d items",
                            path,
                            last_nested_list_id[0],
                            nested_id,
                            len(cast(list[Any], nested_val)),
                        )
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
                    else:
                        logger.debug(
                            "on_root_change: same list identity for path=%s (id=%d), skipping sync",
                            path,
                            nested_id,
                        )
                        # Expand all if requested (QTreeView with expand=True)
                        if expand_on_change and tree_widget is not None:
                            from qtpy.QtCore import QTimer

                            # Defer expandAll to after model updates
                            QTimer.singleShot(0, tree_widget.expandAll)  # type: ignore[attr-defined]
                elif isinstance(nested_val, dict):
                    # Handle dict -> list[(key, value)] conversion for QTableView
                    nested_id = id(cast(dict[Any, Any], nested_val))
                    if nested_id != last_nested_list_id[0]:
                        logger.debug(
                            "on_root_change: dict identity changed for path=%s (old_id=%d, new_id=%d), syncing %d items",
                            path,
                            last_nested_list_id[0],
                            nested_id,
                            len(cast(dict[Any, Any], nested_val)),
                        )
                        last_nested_list_id[0] = nested_id
                        syncing = True
                        try:
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

            root_var.observable.on_change(on_root_change)  # pyright: ignore[reportUnknownMemberType]
            logger.debug("Registered root sync callback for path=%s", path)

        assert root_variable is not None  # Checked in needs_root_sync condition
        make_root_sync_for_model(
            root_variable,
            obs_list,
            nested_path,
            widget_instance if should_expand else None,
            should_expand,
        )

    # Set up selection bindings based on widget type
    if use_tree_model:
        # QTreeView selection bindings
        setup_tree_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_item,
            field_info.selected_items,
            resolve_or_create_variable_fn=resolve_or_create_variable_fn,
        )

        # Handle expand=True: expandAll immediately and on data changes
        if should_expand:
            from qtpy.QtCore import QTimer

            # Expand all immediately after model is set (defer to let model populate)
            QTimer.singleShot(0, widget_instance.expandAll)  # type: ignore[attr-defined]

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
            resolve_or_create_variable_fn=resolve_or_create_variable_fn,
        )
        # Set up embedded widgets for QTableView columns
        if field_info.table_widget_columns:
            _setup_table_widget_columns(host, widget_instance, model, obs_list, field_info.table_widget_columns)
    else:
        # QComboBox/QListView selection bindings
        setup_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_index,
            field_info.selected_item,
            field_info.selected_indexes,
            field_info.selected_items_list,
            resolve_or_create_variable_fn=resolve_or_create_variable_fn,
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
