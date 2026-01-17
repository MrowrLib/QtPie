"""DockWidgetRepeater - Container that manages repeated dock widgets bound to list items."""

from __future__ import annotations

from typing import Any

from observant import Observable, ObservableList, ObservableProxy
from qtpy.QtCore import Qt, QTimer
from qtpy.QtWidgets import QDockWidget, QMainWindow, QWidget

from .dock import Dock
from .repeaters.utils import create_item_wrapper, rebind_child_widgets


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
            selected_item_observable: Observable to sync with selected item.
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
        self._updating_selection = False  # Prevent recursive updates

        # Track: (dock, item_wrapper, index_holder)
        self._items: list[tuple[Dock[W], Observable[Any] | ObservableProxy[Any], list[int]]] = []

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

    def _get_dock_area(self) -> Qt.DockWidgetArea:
        """Convert string dock area to Qt enum."""
        area_map = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }
        return area_map.get(self._dock_area, Qt.DockWidgetArea.RightDockWidgetArea)

    def _resolve_title(self, item: T, wrapper: Observable[Any] | ObservableProxy[Any]) -> str:
        """Resolve title expression for an item."""
        title = self._title_expr

        # Handle {#self} placeholder
        if "{#self}" in title:
            if isinstance(wrapper, Observable):
                value = str(wrapper.get())
            else:
                value = str(wrapper.unwrap())
            title = title.replace("{#self}", value)

        # Handle {property} placeholders for object properties
        if isinstance(wrapper, ObservableProxy):
            import re

            for match in re.finditer(r"\{(\w+)\}", title):
                prop_name = match.group(1)
                if prop_name.startswith("#"):
                    continue  # Skip special placeholders
                prop_obs: Observable[Any] | None = getattr(wrapper, prop_name, None)
                if isinstance(prop_obs, Observable):
                    title = title.replace(f"{{{prop_name}}}", str(prop_obs.get()))

        return title

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

        # Resolve title
        title = self._resolve_title(item, wrapper)

        # Create dock widget
        dock_widget = QDockWidget(title, self._window)
        dock_widget.setWidget(widget)
        dock_widget.setFeatures(self._create_dock_features())

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

        # Insert at correct position
        self._items.insert(index, (dock, wrapper, index_holder))

        # Update indices for items after this one
        for i in range(index + 1, len(self._items)):
            self._items[i][2][0] = i

        # Raise the new tab to front - defer to allow Qt to process tabification
        QTimer.singleShot(0, dock.raise_tab)

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        count_before = len(self._items)
        self._create_and_add_dock(index, item)
        # Set up selection bindings when the second dock is added -
        # that's when Qt creates the tab bar (tabification requires 2+ docks).
        # Note: Use `is not None` because Observable(None) is falsy
        if count_before == 1 and (self._selected_index_obs is not None or self._selected_item_obs is not None):
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
            new_title = self._resolve_title(new_item, wrapper)
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
        """Set up two-way bindings for selectedIndex and selectedItem."""
        # Note: Use `is None` because Observable(None) is falsy
        if self._selected_index_obs is None and self._selected_item_obs is None:
            return

        if not self._items:
            return

        from qtpy.QtWidgets import QTabBar

        # Find the tab bar that contains our docks
        # We need to defer this because the tab bar may not exist until after tabification
        def find_and_bind_tab_bar() -> None:
            if not self._items:
                return

            first_dock = self._items[0][0]
            dock_widget = first_dock.dock_widget

            # Find the tab bar containing this dock
            tab_bar: QTabBar | None = None
            for tb in self._window.findChildren(QTabBar):
                for i in range(tb.count()):
                    if tb.tabText(i) == dock_widget.windowTitle():
                        tab_bar = tb
                        break
                if tab_bar:
                    break

            if not tab_bar:
                return

            # Tab bar -> Observable (when user clicks a tab)
            def on_tab_changed(index: int) -> None:
                if self._updating_selection:
                    return
                self._updating_selection = True
                try:
                    # Find which dock corresponds to this tab
                    if index < 0 or index >= tab_bar.count():  # pyright: ignore[reportPossiblyUnbound]
                        return
                    tab_title = tab_bar.tabText(index)  # pyright: ignore[reportPossiblyUnbound]
                    for i, (dock, _, _) in enumerate(self._items):
                        if dock.dock_widget.windowTitle() == tab_title:
                            # Note: Use `is not None` because Observable(None) is falsy
                            if self._selected_index_obs is not None:
                                self._selected_index_obs.set(i)
                            if self._selected_item_obs is not None:
                                self._selected_item_obs.set(self._obs_list[i])
                            break
                finally:
                    self._updating_selection = False

            tab_bar.currentChanged.connect(on_tab_changed)

            # Observable -> Tab bar (when code changes the selection)
            # Note: Use `is not None` because Observable(None) is falsy
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
                        if self._selected_item_obs is not None:
                            self._selected_item_obs.set(self._obs_list[index])
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
                                break
                    finally:
                        self._updating_selection = False

                self._selected_item_obs.on_change(on_item_changed)

            # Set initial values
            if tab_bar.count() > 0:
                on_tab_changed(tab_bar.currentIndex())

        # Defer binding setup to after Qt event loop processes the tabification
        QTimer.singleShot(0, find_and_bind_tab_bar)
