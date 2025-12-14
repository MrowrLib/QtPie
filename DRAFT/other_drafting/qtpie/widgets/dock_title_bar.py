from typing import override

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class DockTitleBar(QWidget):
    """
    Custom title bar for QDockWidget that provides Windows 11-style behavior:
    - Double-click maximizes/restores the floating dock instead of re-docking
    - Shows title and close button
    - Supports dragging to move the dock
    """

    close_requested = Signal()

    def __init__(self, dock_widget: QDockWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dock_widget = dock_widget
        self._is_maximized = False
        self._normal_geometry = None
        self._drag_start_pos = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(4)

        # Title label
        self._title_label = QLabel(self._dock_widget.windowTitle())
        self._title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._title_label)

        # Close button
        self._close_button = QPushButton("✕")
        self._close_button.setFixedSize(24, 24)
        self._close_button.setFlat(True)
        self._close_button.clicked.connect(self._on_close_clicked)
        self._close_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c42b1c;
                color: white;
            }
        """)
        layout.addWidget(self._close_button)

        # Listen for title changes
        self._dock_widget.windowTitleChanged.connect(self._title_label.setText)

    def _on_close_clicked(self) -> None:
        self.close_requested.emit()
        self._dock_widget.close()

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start_pos is not None and self._dock_widget.isFloating():
            # If maximized and user starts dragging, restore first
            if self._is_maximized:
                self._restore_from_maximize()
                # Adjust drag start to keep cursor in reasonable position on title bar
                self._drag_start_pos = event.globalPosition().toPoint()

            delta = event.globalPosition().toPoint() - self._drag_start_pos
            self._dock_widget.move(self._dock_widget.pos() + delta)
            self._drag_start_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def _toggle_maximize(self) -> None:
        if not self._dock_widget.isFloating():
            # If docked, float it first then maximize
            self._dock_widget.setFloating(True)

        if self._is_maximized:
            self._restore_from_maximize()
        else:
            self._maximize()

    def _maximize(self) -> None:
        # Save current geometry before maximizing
        self._normal_geometry = self._dock_widget.geometry()

        # Get the available screen geometry
        screen = self._dock_widget.screen()
        if screen:
            available = screen.availableGeometry()
            self._dock_widget.setGeometry(available)

        self._is_maximized = True

    def _restore_from_maximize(self) -> None:
        if self._normal_geometry:
            self._dock_widget.setGeometry(self._normal_geometry)
        self._is_maximized = False

    @override
    def event(self, event: QEvent) -> bool:
        # Reset maximized state when dock is re-docked
        if event.type() == QEvent.Type.WindowStateChange:
            if not self._dock_widget.isFloating():
                self._is_maximized = False
        return super().event(event)
