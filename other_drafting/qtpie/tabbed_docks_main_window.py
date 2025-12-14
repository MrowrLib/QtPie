from typing import Callable, cast, override

from PySide6.QtCore import QEvent, QObject, QPoint
from PySide6.QtGui import QMouseEvent, Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow, QTabBar, QTabWidget, QWidget

from qtpie.signal_typing import as_bool_handler


class TabbedDocksMainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._docked_widgets: list[QDockWidget] = []
        self._on_tab_close_requested: Callable[[int], None] | None = None
        self._drag_tab_start_pos: QPoint = QPoint()
        self._drag_tab_index: int = -1
        self._drag_tab_text: str | None = None
        self.setDockNestingEnabled(True)
        self.setTabPosition(Qt.DockWidgetArea.AllDockWidgetAreas, QTabWidget.TabPosition.North)

    @override
    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.LayoutRequest:
            self._install_tab_features()
        return super().event(event)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QTabBar):
            tab_bar = watched
            if event.type() == QEvent.Type.MouseButtonPress:
                mouse_event = cast(QMouseEvent, event)
                self._drag_tab_start_pos = mouse_event.pos()
                self._drag_tab_index = tab_bar.tabAt(self._drag_tab_start_pos)
                if self._drag_tab_index >= 0:
                    self._drag_tab_text = tab_bar.tabText(self._drag_tab_index)
            elif event.type() == QEvent.Type.MouseMove and self._drag_tab_text is not None:
                mouse_event = cast(QMouseEvent, event)
                margin = 50
                padded = tab_bar.rect().adjusted(-margin, -margin, margin, margin)
                if not padded.contains(mouse_event.pos()):
                    self._undock_tab(self._drag_tab_text)
                    self._drag_tab_text = None
            elif event.type() in {QEvent.Type.MouseButtonRelease, QEvent.Type.Leave}:
                self._drag_tab_text = None
        return super().eventFilter(watched, event)

    def _install_tab_features(self) -> None:
        for tab_bar in self.findChildren(QTabBar):
            if not tab_bar.property("_customized"):
                tab_bar.setTabsClosable(True)
                tab_bar.setMovable(True)
                tab_bar.tabCloseRequested.connect(self.on_tab_close)
                tab_bar.installEventFilter(self)
                tab_bar.setProperty("_customized", True)

    def _undock_tab(self, tab_text: str) -> None:
        for dock in self.findChildren(QDockWidget):
            if dock.windowTitle() == tab_text:
                siblings = self.tabifiedDockWidgets(dock)
                self.removeDockWidget(dock)
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
                dock.setFloating(True)
                dock.show()

                # Update all previously tabified docks (including the undocked one)
                for d in siblings + [dock]:
                    self._update_title_bar_for(d)
                break

    # NOTE: we should handle other close methods to keep docked_widgets in sync
    def on_tab_close(self, index: int) -> None:
        print(f"Tab close requested: {index}")

    def hide_titlebar(self, dock_widget: QDockWidget) -> None:
        hidden = QWidget()
        hidden.setFixedHeight(0)
        dock_widget.setTitleBarWidget(hidden)

    def show_titlebar(self, dock_widget: QDockWidget) -> None:
        current = dock_widget.titleBarWidget()
        # Only reset if it's a hidden (zero-height) title bar, not a custom one
        if current is not None and current.sizeHint().height() == 0:
            dock_widget.setTitleBarWidget(None)  # type: ignore

    def _update_title_bar_for(self, dock: QDockWidget) -> None:
        tab_group = self.tabifiedDockWidgets(dock)
        if dock not in tab_group:
            tab_group.append(dock)

        for w in tab_group:
            is_tabbified = any(other in self.tabifiedDockWidgets(w) for other in self.findChildren(QDockWidget) if other is not w)
            if is_tabbified:
                current = w.titleBarWidget()
                if current is None or current.sizeHint().height() > 0:  # type: ignore
                    self.hide_titlebar(w)
            else:
                self.show_titlebar(w)

    def _make_dock(
        self,
        widget: QWidget,
        title: str | None = None,
        allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
        features: QDockWidget.DockWidgetFeature = QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable,
    ) -> QDockWidget:
        dock = QDockWidget(title or widget.windowTitle(), self)
        dock.setWidget(widget)
        dock.setAllowedAreas(allowed_areas)
        dock.setFeatures(features)
        dock.topLevelChanged.connect(as_bool_handler(lambda _: self._update_title_bar_for(dock)))
        dock.dockLocationChanged.connect(as_bool_handler(lambda _: self._update_title_bar_for(dock)))
        widget.windowTitleChanged.connect(as_bool_handler(lambda title: dock.setWindowTitle(widget.windowTitle())))
        self._docked_widgets.append(dock)
        return dock

    def dock(
        self,
        widget: QWidget,
        area: Qt.DockWidgetArea,
        title: str | None = None,
        allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
        features: QDockWidget.DockWidgetFeature = QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable,
    ) -> QDockWidget:
        dock = self._make_dock(widget, title, allowed_areas, features)
        self.addDockWidget(area, dock)
        return dock

    # def on_tab_close(self, callback: Callable[[int], None]) -> None:
    #     self._on_tab_close_requested = callback
