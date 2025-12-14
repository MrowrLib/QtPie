from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, cast, override

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QTabBar,
    QTabWidget,
    QWidget,
)

from qtpie.signal_typing import as_bool_handler

# This is lovely, but very much a draft for now I feel like still...

# TODO: after we set a widget as floating, from dragging from the tab bar,
# after it becomes floating perform a "click" on the title bar of the widget so we can keep dragging it, if possible


class IDockManager(ABC):
    @abstractmethod
    def on_tab_close(self, callback: Callable[[int], None]) -> None: ...

    @abstractmethod
    def get_docked_widgets(self) -> list[QDockWidget]: ...

    @abstractmethod
    def on_event(self, event: QEvent) -> None: ...

    @abstractmethod
    def on_eventFilter(self, watched: QObject, event: QEvent) -> None: ...

    @abstractmethod
    def hide_titlebar(self, dock_widget: QDockWidget) -> None: ...

    @abstractmethod
    def show_titlebar(self, dock_widget: QDockWidget) -> None: ...

    @abstractmethod
    def dock(
        self,
        widget: QWidget,
        area: Qt.DockWidgetArea,
        # *,
        title: str | None = None,
        allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
        features: QDockWidget.DockWidgetFeature = QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable,
    ) -> QDockWidget: ...

    # def make_dock(
    #     self,
    #     widget: QWidget,
    #     area: Qt.DockWidgetArea,
    #     *,
    #     title: str | None = None,
    #     allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
    #     features: QDockWidget.DockWidgetFeature = QDockWidget.DockWidgetFeature.DockWidgetClosable
    #     | QDockWidget.DockWidgetFeature.DockWidgetMovable
    #     | QDockWidget.DockWidgetFeature.DockWidgetFloatable,
    # ) -> QDockWidget: ...


@dataclass
class DockManager(IDockManager):
    main_window: QMainWindow
    docked_widgets: list[QDockWidget] = field(default_factory=list[QDockWidget])

    _on_tab_close_requested: Callable[[int], None] | None = None
    _drag_tab_start_pos: QPoint = field(default_factory=QPoint)
    _drag_tab_index: int = -1
    _drag_tab_text: str | None = None

    def __post_init__(self) -> None:
        self.main_window.setDockNestingEnabled(True)
        self.main_window.setTabPosition(Qt.DockWidgetArea.AllDockWidgetAreas, QTabWidget.TabPosition.North)

    @override
    def on_tab_close(self, callback: Callable[[int], None]) -> None:
        self._on_tab_close_requested = callback

    @override
    def get_docked_widgets(self) -> list[QDockWidget]:
        """Get the list of docked widgets."""
        return self.docked_widgets

    @override
    def on_event(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LayoutRequest:
            self._install_tab_features()

    @override
    def on_eventFilter(self, watched: QObject, event: QEvent) -> None:
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

    def _install_tab_features(self) -> None:
        for tab_bar in self.main_window.findChildren(QTabBar):
            if not tab_bar.property("_customized"):
                tab_bar.setTabsClosable(True)
                tab_bar.setMovable(True)
                tab_bar.tabCloseRequested.connect(self._handle_tab_close)
                tab_bar.installEventFilter(self.main_window)
                tab_bar.setProperty("_customized", True)

    # NOTE: we should handle other close methods to keep docked_widgets in sync
    def _handle_tab_close(self, index: int) -> None:
        if self._on_tab_close_requested:
            self._on_tab_close_requested(index)

    # @override
    def _make_dock(
        self,
        widget: QWidget,
        title: str | None = None,
        allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
        features: QDockWidget.DockWidgetFeature = QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable,
    ) -> QDockWidget:
        dock = QDockWidget(title or widget.windowTitle(), self.main_window)
        dock.setWidget(widget)
        dock.setAllowedAreas(allowed_areas)

        dock.setFeatures(features)
        dock.topLevelChanged.connect(as_bool_handler(lambda _: self._update_title_bar_for(dock)))
        dock.dockLocationChanged.connect(as_bool_handler(lambda _: self._update_title_bar_for(dock)))
        widget.windowTitleChanged.connect(as_bool_handler(lambda title: dock.setWindowTitle(widget.windowTitle())))
        self.docked_widgets.append(dock)
        return dock

    @override
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
        self.main_window.addDockWidget(area, dock)
        return dock

    def _undock_tab(self, tab_text: str) -> None:
        for dock in self.main_window.findChildren(QDockWidget):
            if dock.windowTitle() == tab_text:
                siblings = self.main_window.tabifiedDockWidgets(dock)
                self.main_window.removeDockWidget(dock)
                self.main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
                dock.setFloating(True)
                dock.show()

                # Update all previously tabified docks (including the undocked one)
                for d in siblings + [dock]:
                    self._update_title_bar_for(d)
                break

    @override
    def hide_titlebar(self, dock_widget: QDockWidget) -> None:
        hidden = QWidget()
        hidden.setFixedHeight(0)
        dock_widget.setTitleBarWidget(hidden)

    @override
    def show_titlebar(self, dock_widget: QDockWidget) -> None:
        dock_widget.setTitleBarWidget(None)  # type: ignore

    def _update_title_bar_for(self, dock: QDockWidget) -> None:
        tab_group = self.main_window.tabifiedDockWidgets(dock)
        if dock not in tab_group:
            tab_group.append(dock)

        for w in tab_group:
            is_tabbified = any(other in self.main_window.tabifiedDockWidgets(w) for other in self.main_window.findChildren(QDockWidget) if other is not w)
            if is_tabbified:
                current = w.titleBarWidget()
                if current is None or current.sizeHint().height() > 0:  # type: ignore
                    self.hide_titlebar(w)
            else:
                self.show_titlebar(w)


def get_dock_manager(main_window: QMainWindow) -> IDockManager:
    """Get the Dock Manager for the given QMainWindow."""
    return DockManager(main_window)
