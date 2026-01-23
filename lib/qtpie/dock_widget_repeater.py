"""DockWidgetRepeater - Container that manages repeated dock widgets bound to list items."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, cast, override

from observant import Observable, ObservableList, ObservableProxy
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import QDockWidget, QMainWindow, QWidget

from .bindings.format_binding import (
    _extract_ast_names,  # pyright: ignore[reportPrivateUsage]
    _parse_format_fields,  # pyright: ignore[reportPrivateUsage]
    create_item_formatter_with_context,
)
from .dock import Dock
from .repeaters.utils import create_item_wrapper, rebind_child_widgets
from .variable import Variable


class DockWidgetRepeater[T, W: QWidget]:
    """Container that manages repeated dock widgets bound to list items.

    Creates one Dock[W] per list item. Uses granular callbacks (on_insert,
    on_remove, on_replace, on_clear) to efficiently sync the dock list
    with the underlying ObservableList.

    Docks in the same group are automatically tabified together.

    Usage:
        open_requests: Variable[list[Request]] = new([])
        _editors: list[Dock[RequestEditorWidget]] = new(
            bind="open_requests",
            dock="right",
            group="editors",
            title="{name}",
        )
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        item_type: type | None,
        widget_type: type[W],
        window: QMainWindow,
        dock_area: str = "right",
        group: str | None = None,
        title: str = "{#self}",
        closable: bool = True,
        floatable: bool = True,
        movable: bool = True,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        selected_index_observable: Observable[int] | None = None,
        selected_item_observable: Observable[T | None] | None = None,
        selected_item_variable: Variable[T | None] | None = None,
        selected_dock_observable: Observable[Dock[W] | None] | None = None,
        selected_index_changed_callback: Callable[[int], None] | None = None,
        selected_item_changed_callback: Callable[[T | None], None] | None = None,
        selected_dock_changed_callback: Callable[[Dock[W] | None], None] | None = None,
        initial_visible: bool = True,
        context_menu: type | None = None,
    ) -> None:
        """Initialize the dock widget repeater.

        Args:
            observable_list: The ObservableList to sync with.
            item_type: The type of items in the list.
            widget_type: The widget type to create for each dock.
            window: The parent Window instance.
            dock_area: Dock area ("left", "right", "top", "bottom").
            group: Group name for tabifying docks together.
            title: Title expression (can include {name}, {#self}, etc).
            closable: Whether docks can be closed.
            floatable: Whether docks can be floated.
            movable: Whether docks can be moved.
            widget_args: Positional args for widget constructor.
            widget_kwargs: Keyword args for widget constructor.
            selected_index_observable: Observable to sync with selected tab index.
            selected_item_observable: Observable to sync with selected item (value only).
            selected_item_variable: Variable to sync with selected item (shares wrapper/proxy).
            selected_dock_observable: Observable to sync with selected dock wrapper.
            selected_index_changed_callback: Callback when selected index changes.
            selected_item_changed_callback: Callback when selected item changes.
            selected_dock_changed_callback: Callback when selected dock changes.
            initial_visible: Initial visibility state for all docks in the group.
            context_menu: Custom context menu class for docks in this repeater.
        """
        self._obs_list = observable_list
        self._item_type = item_type
        self._widget_type = widget_type
        self._window = window
        self._dock_area = dock_area
        self._group = group
        self._title_expr = title
        self._closable = closable
        self._floatable = floatable
        self._movable = movable
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._selected_index_obs = selected_index_observable
        self._selected_item_obs = selected_item_observable
        self._selected_item_var = selected_item_variable
        self._selected_dock_obs = selected_dock_observable
        self._selected_index_changed_cb = selected_index_changed_callback
        self._selected_item_changed_cb = selected_item_changed_callback
        self._selected_dock_changed_cb = selected_dock_changed_callback
        self._updating_selection = False  # Prevent recursive updates
        self._group_visible = initial_visible  # Track group visibility
        self._context_menu = context_menu  # Custom context menu class

        # Track: (dock, item_wrapper, index_holder)
        self._items: list[tuple[Dock[W], Observable[Any] | ObservableProxy[Any], list[int]]] = []

        # Create title formatter using the real format binding system
        self._title_formatter = create_item_formatter_with_context(title)

        # Create initial docks for existing items
        for i, item in enumerate(observable_list):
            self._create_and_add_dock(i, item)

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

        # Set up selection bindings after initial docks are created
        self._setup_selection_bindings()

    def set_group_visible(self, visible: bool) -> None:
        """Set visibility of all docks in the group.

        This affects all existing docks and any new docks added in the future.

        Args:
            visible: Whether the docks should be visible.
        """
        self._group_visible = visible
        for dock, _, _ in self._items:
            dock_widget = dock.dock_widget
            if visible and dock_widget.isHidden():
                dock_widget.setVisible(True)
            elif not visible and not dock_widget.isHidden():
                dock_widget.setVisible(False)

    def _get_dock_area(self) -> Qt.DockWidgetArea:
        """Convert string dock area to Qt enum."""
        area_map = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }
        return area_map.get(self._dock_area, Qt.DockWidgetArea.RightDockWidgetArea)

    def _resolve_title(self, item: T, widget: W | None = None) -> str:
        """Resolve title expression for an item using the format binding system."""
        context: dict[str, Any] = {}
        if widget is not None:
            context["widget"] = widget
        return self._title_formatter(item, context)

    def _subscribe_to_title_changes(
        self,
        item: T,
        wrapper: Observable[Any] | ObservableProxy[Any],
        dock_widget: QDockWidget,
        widget: W,
    ) -> None:
        """Subscribe to all observables referenced in title and update reactively."""

        def update_title() -> None:
            if isinstance(wrapper, Observable):
                new_title = self._resolve_title(wrapper.get(), widget)
            else:
                new_title = self._resolve_title(wrapper.unwrap(), widget)
            dock_widget.setWindowTitle(new_title)

        # Subscribe to item wrapper changes
        if isinstance(wrapper, Observable):
            wrapper.on_change(lambda _: update_title())
        else:
            wrapper.on_change(update_title)

        # Parse title expression to find all referenced names
        fields = _parse_format_fields(self._title_expr)
        all_names: set[str] = set()
        for field in fields:
            # Normalize #widget to widget_ref for AST parsing
            expr = field.expression.replace("#widget", "widget_ref").replace("#self", "self_ref")
            all_names.update(_extract_ast_names(expr))

        # Find observables on the widget (for #widget.* references)
        if "widget_ref" in all_names:
            # Look for any Observable attributes on the widget that are referenced
            # Parse expressions like "widget_ref.is_dirty" to find "is_dirty"
            for field in fields:
                expr = field.expression
                if "#widget" in expr:
                    # Find all #widget.attr patterns
                    for match in re.finditer(r"#widget\.(\w+)", expr):
                        attr_name = match.group(1)
                        if hasattr(widget, attr_name):
                            attr = getattr(widget, attr_name)
                            if isinstance(attr, Observable):
                                attr.on_change(lambda _val: update_title())  # pyright: ignore[reportUnknownLambdaType,reportUnknownMemberType]
                            elif isinstance(attr, (ObservableList, ObservableProxy)):
                                attr.on_change(update_title)

    def _create_dock_features(self) -> QDockWidget.DockWidgetFeature:
        """Create dock widget features flags."""
        features = QDockWidget.DockWidgetFeature(0)
        if self._closable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
        if self._floatable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetFloatable
        if self._movable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetMovable
        return features

    def _set_selected_item(self, idx: int) -> None:
        """Set the selected item by index.

        If a Variable was provided (selected_item_variable), this swaps the wrapper
        to share the ObservableProxy with the widget, preserving dirty/valid state.
        Otherwise, falls back to setting the value via the Observable.
        """
        if idx < 0 or idx >= len(self._items):
            return

        _, wrapper, _ = self._items[idx]

        # If we have a Variable, swap its wrapper to share the proxy (preserves dirty state)
        if self._selected_item_var is not None and isinstance(wrapper, ObservableProxy):
            self._selected_item_var.replace_wrapper(wrapper)
        # Fall back to setting value via Observable (old behavior)
        elif self._selected_item_obs is not None:
            self._selected_item_obs.set(self._obs_list[idx])

    def _setup_dock_focus_tracking(self, dock: Dock[W], index_holder: list[int]) -> None:
        """Set up focus tracking for docks.

        When any widget inside a dock gains focus or the dock's title bar is clicked,
        update the selection bindings to reflect that this dock is now "selected".
        This works for floating docks, tabified docks, and standalone docks.
        """
        # Skip if no selection bindings or callbacks are configured
        has_bindings = self._selected_index_obs is not None or self._selected_item_obs is not None or self._selected_item_var is not None or self._selected_dock_obs is not None
        has_callbacks = self._selected_index_changed_cb is not None or self._selected_item_changed_cb is not None or self._selected_dock_changed_cb is not None
        if not has_bindings and not has_callbacks:
            return

        dock_widget = dock.dock_widget

        def update_selection() -> None:
            """Update selection to this dock."""
            if self._updating_selection:
                return

            idx = index_holder[0]
            if idx < 0 or idx >= len(self._items):
                return

            self._updating_selection = True
            try:
                if self._selected_index_obs is not None:
                    self._selected_index_obs.set(idx)
                self._set_selected_item(idx)
                if self._selected_dock_obs is not None:
                    self._selected_dock_obs.set(dock)
                # Fire callbacks
                if self._selected_index_changed_cb is not None:
                    self._selected_index_changed_cb(idx)
                if self._selected_item_changed_cb is not None:
                    self._selected_item_changed_cb(self._obs_list[idx])
                if self._selected_dock_changed_cb is not None:
                    self._selected_dock_changed_cb(dock)
            finally:
                self._updating_selection = False

        def on_focus_changed(old: QWidget | None, new: QWidget | None) -> None:
            # Check if focus moved to this dock (floating or not)
            if new is None:
                return
            if not dock_widget.isAncestorOf(new) and new is not dock_widget:
                return
            update_selection()

        # Track focus changes for this dock's content
        from qtpy.QtCore import QEvent, QObject
        from qtpy.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None and isinstance(app, QApplication):
            app.focusChanged.connect(on_focus_changed)

        # Also track clicks on the dock widget itself (including title bar)
        class DockClickFilter(QObject):
            @override
            def eventFilter(self_, watched: QObject, event: QEvent) -> bool:
                if event.type() == QEvent.Type.MouseButtonPress:
                    update_selection()
                return False

        click_filter = DockClickFilter(dock_widget)
        dock_widget.installEventFilter(click_filter)

    def _create_and_add_dock(self, index: int, item: T) -> None:
        """Create a dock for an item and add it to the window."""
        wrapper = create_item_wrapper(item, self._item_type)
        index_holder = [index]

        # Create the content widget
        widget = self._widget_type(*self._widget_args, **self._widget_kwargs)

        # If the widget is a Widget[T] with a record type, assign the wrapper as its record
        # This ensures the widget and the repeater share the same ObservableProxy,
        # so changes in the widget are reflected in the title and vice versa
        widget_config = getattr(type(widget), "_qtpie_config", None)
        if widget_config is not None and getattr(widget_config, "record_type", None) is not None:
            from .bindings.apply import apply_auto_bindings
            from .variable import RecordVariable

            if isinstance(wrapper, ObservableProxy):
                # Pass the existing proxy wrapped in a RecordVariable
                record_var: RecordVariable[Any] = RecordVariable(wrapper)
                widget.record = record_var  # type: ignore[union-attr]
            else:
                # Primitive type - just set the value directly
                widget.record = item  # type: ignore[union-attr]

            # Re-apply auto-bindings now that record is populated
            # This is needed because the widget's __init__ ran before we set up the record
            apply_auto_bindings(widget, widget_config)  # type: ignore[arg-type]

            # Also re-apply bindings on child Widget[T] instances that bind to parent's record
            rebind_child_widgets(widget)

        # Resolve title (pass widget for #widget.* placeholders)
        title = self._resolve_title(item, widget)

        # Create dock widget
        dock_widget = QDockWidget(title, self._window)
        dock_widget.setWidget(widget)
        dock_widget.setFeatures(self._create_dock_features())

        # Store custom context menu class as property for DockTabEventFilter to find
        if self._context_menu is not None:
            dock_widget.setProperty("_qtpie_context_menu", self._context_menu)

        # Subscribe to title property changes for reactive updates
        self._subscribe_to_title_changes(item, wrapper, dock_widget, widget)

        # Add to window
        main_window: QMainWindow = self._window
        area = self._get_dock_area()

        # Tabify with existing docks in the same group
        if self._group and self._items:
            # Add to the same area as first dock
            main_window.addDockWidget(area, dock_widget)
            # Tabify with first existing dock
            first_dock = self._items[0][0]
            main_window.tabifyDockWidget(first_dock.dock_widget, dock_widget)
        else:
            main_window.addDockWidget(area, dock_widget)

        # Create Dock wrapper
        dock: Dock[W] = Dock(widget, dock_widget)

        # Handle dock close - remove from list when user clicks X button
        # We install an event filter to detect the actual close event, not visibility changes
        # (visibilityChanged fires on tab switches too, which we don't want)
        from qtpy.QtCore import QEvent, QObject

        class CloseFilter(QObject):
            def __init__(self, repeater: DockWidgetRepeater[Any, Any], idx: list[int], parent: QObject | None = None) -> None:
                super().__init__(parent)
                self._repeater = repeater
                self._idx = idx

            def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:  # pyright: ignore[reportImplicitOverride]
                if event is not None and event.type() == QEvent.Type.Close:
                    # Dock is being closed - remove from list
                    # Check for -1 which indicates this was already removed via _on_remove
                    if self._idx[0] >= 0 and self._idx[0] < len(self._repeater._obs_list):
                        del self._repeater._obs_list[self._idx[0]]
                    return False  # Don't block the close
                return False

        close_filter = CloseFilter(self, index_holder, dock_widget)
        dock_widget.installEventFilter(close_filter)

        # Set up focus tracking (selection updates when dock gains focus, floating or not)
        self._setup_dock_focus_tracking(dock, index_holder)

        # Insert at correct position
        self._items.insert(index, (dock, wrapper, index_holder))

        # Update indices for items after this one
        for i in range(index + 1, len(self._items)):
            self._items[i][2][0] = i

        # Apply group visibility to the new dock
        if not self._group_visible:
            dock_widget.setVisible(False)

        # Raise the new tab to front - defer to allow Qt to process tabification
        QTimer.singleShot(0, dock.raise_tab)

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        count_before = len(self._items)
        self._create_and_add_dock(index, item)
        # Set up selection bindings when the second dock is added -
        # that's when Qt creates the tab bar (tabification requires 2+ docks).
        # Note: Use `is not None` because Observable(None) is falsy
        has_bindings_or_callbacks = (
            self._selected_index_obs is not None
            or self._selected_item_obs is not None
            or self._selected_item_var is not None
            or self._selected_dock_obs is not None
            or self._selected_index_changed_cb is not None
            or self._selected_item_changed_cb is not None
            or self._selected_dock_changed_cb is not None
        )
        if count_before == 1 and has_bindings_or_callbacks:
            self._setup_selection_bindings()

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        if index < len(self._items):
            dock, _, index_holder = self._items.pop(index)

            # Invalidate the index holder so the CloseFilter won't try to
            # delete from the list again (which would cause a cascade delete)
            index_holder[0] = -1

            # Remove and delete dock widget
            dock.dock_widget.close()
            dock.dock_widget.deleteLater()

            # Update indices for remaining items
            for i in range(index, len(self._items)):
                self._items[i][2][0] = i

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        if index < len(self._items):
            dock, wrapper, index_holder = self._items[index]

            # Update wrapper value
            if isinstance(wrapper, Observable):
                wrapper.set(new_item)
            else:
                # For complex objects, update the proxy's underlying value
                # This requires recreating the dock
                self._on_remove(index, old_item)
                self._items.insert(index, (dock, wrapper, index_holder))  # Placeholder
                self._on_insert(index, new_item)
                return

            # Update title
            new_title = self._resolve_title(new_item, dock.widget)
            dock.dock_widget.setWindowTitle(new_title)

    def _on_clear(self, removed_items: list[T]) -> None:
        """Handle list clear."""
        # Remove all docks
        for dock, _, _ in self._items:
            dock.dock_widget.close()
            dock.dock_widget.deleteLater()
        self._items.clear()

    def dock_at(self, index: int) -> Dock[W] | None:
        """Get the dock at a specific index."""
        if 0 <= index < len(self._items):
            return self._items[index][0]
        return None

    def dock_count(self) -> int:
        """Get the number of docks."""
        return len(self._items)

    @property
    def docks(self) -> list[Dock[W]]:
        """Get all docks as a list."""
        return [d for d, _, _ in self._items]

    # List-like interface
    def __getitem__(self, index: int) -> Dock[W]:
        """Get dock at index (list-like access)."""
        if index < 0:
            index = len(self._items) + index
        if 0 <= index < len(self._items):
            return self._items[index][0]
        raise IndexError(f"index {index} out of range")

    def __len__(self) -> int:
        """Return number of docks."""
        return len(self._items)

    def __iter__(self):
        """Iterate over docks."""
        for dock, _, _ in self._items:
            yield dock

    def _setup_selection_bindings(self) -> None:
        """Set up two-way bindings for selectedIndex, selectedItem, and selectedDock."""
        # Note: Use `is None` because Observable(None) is falsy
        has_bindings = self._selected_index_obs is not None or self._selected_item_obs is not None or self._selected_item_var is not None or self._selected_dock_obs is not None
        has_callbacks = self._selected_index_changed_cb is not None or self._selected_item_changed_cb is not None or self._selected_dock_changed_cb is not None
        if not has_bindings and not has_callbacks:
            return

        if not self._items:
            return

        from qtpy.QtCore import QEvent, QObject
        from qtpy.QtWidgets import QTabBar

        # Track which tab bars we've already connected to
        connected_tab_bars: set[int] = set()  # Use id() since QTabBar isn't hashable

        # Handler for tab changes - fires selection callbacks
        def on_tab_changed(tab_bar: QTabBar, index: int) -> None:
            if self._updating_selection:
                return
            self._updating_selection = True
            try:
                if index < 0 or index >= tab_bar.count():
                    return
                tab_title = tab_bar.tabText(index)
                for i, (dock, _, _) in enumerate(self._items):
                    if dock.dock_widget.windowTitle() == tab_title:
                        if self._selected_index_obs is not None:
                            self._selected_index_obs.set(i)
                        self._set_selected_item(i)
                        if self._selected_dock_obs is not None:
                            self._selected_dock_obs.set(dock)
                        if self._selected_index_changed_cb is not None:
                            self._selected_index_changed_cb(i)
                        if self._selected_item_changed_cb is not None:
                            self._selected_item_changed_cb(self._obs_list[i])
                        if self._selected_dock_changed_cb is not None:
                            self._selected_dock_changed_cb(dock)
                        break
            finally:
                self._updating_selection = False

        def find_and_bind_new_tab_bars() -> None:
            """Find any tab bars containing our docks and connect to them."""
            if not self._items:
                return

            # Get all dock titles we care about
            our_dock_titles = {dock.dock_widget.windowTitle() for dock, _, _ in self._items}

            for tab_bar in self._window.findChildren(QTabBar):
                tb_id = id(tab_bar)
                if tb_id in connected_tab_bars:
                    continue

                # Check if this tab bar contains any of our docks
                has_our_dock = False
                for i in range(tab_bar.count()):
                    if tab_bar.tabText(i) in our_dock_titles:
                        has_our_dock = True
                        break

                if has_our_dock:
                    connected_tab_bars.add(tb_id)

                    # Create a closure to capture tab_bar
                    def make_handler(tb: QTabBar) -> Callable[[int], None]:
                        def handler(idx: int) -> None:
                            on_tab_changed(tb, idx)

                        return handler

                    tab_bar.currentChanged.connect(make_handler(tab_bar))

                    # Also install event filter to catch clicks on already-selected tabs
                    # (currentChanged won't fire if clicking the already-selected tab)
                    def make_click_filter(tb: QTabBar) -> QObject:
                        class TabClickFilter(QObject):
                            @override
                            def eventFilter(self_, watched: QObject, event: QEvent) -> bool:
                                if event.type() == QEvent.Type.MouseButtonPress:
                                    from qtpy.QtGui import QMouseEvent

                                    mouse_event = cast(QMouseEvent, event)
                                    clicked_index = tb.tabAt(mouse_event.pos())
                                    # Only fire if clicking the already-selected tab
                                    # (otherwise currentChanged will handle it)
                                    if clicked_index >= 0 and clicked_index == tb.currentIndex():
                                        on_tab_changed(tb, clicked_index)
                                return False

                        return TabClickFilter(tb)

                    tab_bar.installEventFilter(make_click_filter(tab_bar))

        # Event filter to detect layout changes and bind to new tab bars
        class TabBarWatcher(QObject):
            @override
            def eventFilter(self, watched: QObject, event: QEvent) -> bool:
                if event.type() == QEvent.Type.LayoutRequest:
                    find_and_bind_new_tab_bars()
                return False

        watcher = TabBarWatcher(self._window)
        self._window.installEventFilter(watcher)

        # Observable -> Tab bar (when code changes the selection)
        if self._selected_index_obs is not None:

            def on_index_changed(index: int) -> None:
                if self._updating_selection:
                    return
                if index < 0 or index >= len(self._items):
                    return
                self._updating_selection = True
                try:
                    dock = self._items[index][0]
                    dock.raise_tab()
                    self._set_selected_item(index)
                    if self._selected_dock_obs is not None:
                        self._selected_dock_obs.set(dock)
                finally:
                    self._updating_selection = False

            self._selected_index_obs.on_change(on_index_changed)

        if self._selected_item_obs is not None:

            def on_item_changed(item: T | None) -> None:
                if self._updating_selection:
                    return
                if item is None:
                    return
                self._updating_selection = True
                try:
                    # Find the index of this item
                    for i, list_item in enumerate(self._obs_list):
                        if list_item is item or list_item == item:
                            dock = self._items[i][0]
                            dock.raise_tab()
                            if self._selected_index_obs is not None:
                                self._selected_index_obs.set(i)
                            if self._selected_dock_obs is not None:
                                self._selected_dock_obs.set(dock)
                            break
                finally:
                    self._updating_selection = False

            self._selected_item_obs.on_change(on_item_changed)

        if self._selected_dock_obs is not None:

            def on_dock_changed(dock: Dock[W] | None) -> None:
                if self._updating_selection:
                    return
                if dock is None:
                    return
                self._updating_selection = True
                try:
                    # Find the index of this dock
                    for i, (d, _, _) in enumerate(self._items):
                        if d is dock:
                            d.raise_tab()
                            if self._selected_index_obs is not None:
                                self._selected_index_obs.set(i)
                            self._set_selected_item(i)
                            break
                finally:
                    self._updating_selection = False

            self._selected_dock_obs.on_change(on_dock_changed)

        # Do initial binding and set initial values
        def initialize() -> None:
            find_and_bind_new_tab_bars()

            # Set initial values silently (don't fire callbacks)
            if self._items:
                # Find the first visible/selected dock
                for tab_bar in self._window.findChildren(QTabBar):
                    our_dock_titles = {dock.dock_widget.windowTitle() for dock, _, _ in self._items}
                    for j in range(tab_bar.count()):
                        if tab_bar.tabText(j) in our_dock_titles:
                            # Found a tab bar with our docks
                            initial_index = tab_bar.currentIndex()
                            if initial_index >= 0:
                                tab_title = tab_bar.tabText(initial_index)
                                for i, (dock, _, _) in enumerate(self._items):
                                    if dock.dock_widget.windowTitle() == tab_title:
                                        if self._selected_index_obs is not None:
                                            self._selected_index_obs._value = i  # pyright: ignore[reportPrivateUsage]
                                        if self._selected_item_obs is not None:
                                            self._selected_item_obs._value = self._obs_list[i]  # pyright: ignore[reportPrivateUsage]
                                        if self._selected_dock_obs is not None:
                                            self._selected_dock_obs._value = dock  # pyright: ignore[reportPrivateUsage]
                                        return
                            break

        # Defer to after Qt event loop processes the tabification
        QTimer.singleShot(0, initialize)
