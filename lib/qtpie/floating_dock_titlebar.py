"""Custom title bar for floating dock widgets.

This module provides a custom title bar widget that can be used with floating
QDockWidgets to intercept double-click events. The native OS title bar handles
double-clicks at the window manager level, making them impossible to intercept
with Qt event filters.
"""

import logging
import sys
from typing import override

from qtpy.QtCore import QPoint, Qt, QTimer
from qtpy.QtGui import QMouseEvent
from qtpy.QtWidgets import QDockWidget, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget

logger = logging.getLogger(__name__)


def _debug(msg: str) -> None:
    """Debug log with immediate flush to catch crashes."""
    logger.debug(msg)
    for handler in logging.root.handlers + logger.handlers:
        handler.flush()
    sys.stderr.flush()
    sys.stdout.flush()


class FloatingDockTitleBar(QWidget):
    """Custom title bar for floating dock widgets.

    Provides:
    - Title label that updates when dock title changes
    - Dragging to move the floating dock
    - Close button (if dock is closable)
    - Float button to dock the widget back (if dock is floatable)
    - Double-click handling via event filter
    """

    def __init__(self, dock: QDockWidget) -> None:
        super().__init__(dock)
        dock_title = dock.windowTitle()
        _debug(f"FloatingDockTitleBar.__init__: dock={dock_title!r}")
        self._dock = dock
        self._drag_start_pos: QPoint | None = None

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Title label
        self._title_label = QLabel(dock.windowTitle())
        self._title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._title_label)

        # Float button (dock back)
        features = dock.features()
        if features & QDockWidget.DockWidgetFeature.DockWidgetFloatable:
            self._float_btn = QToolButton()
            self._float_btn.setText("\u25a3")  # Unicode square with inner square
            self._float_btn.setToolTip("Dock")
            self._float_btn.setAutoRaise(True)
            self._float_btn.clicked.connect(self._on_float_clicked)
            layout.addWidget(self._float_btn)

        # Close button
        if features & QDockWidget.DockWidgetFeature.DockWidgetClosable:
            self._close_btn = QToolButton()
            self._close_btn.setText("\u00d7")  # Unicode multiplication sign (X)
            self._close_btn.setToolTip("Close")
            self._close_btn.setAutoRaise(True)
            self._close_btn.clicked.connect(dock.close)
            layout.addWidget(self._close_btn)

        # Connect to title changes
        dock.windowTitleChanged.connect(self._title_label.setText)

        # Style to look more like a title bar
        self.setStyleSheet("""
            FloatingDockTitleBar {
                background-color: palette(window);
                border-bottom: 1px solid palette(mid);
            }
            QLabel {
                font-weight: bold;
            }
            QToolButton {
                border: none;
                padding: 2px 6px;
            }
            QToolButton:hover {
                background-color: palette(midlight);
            }
        """)

    def _on_float_clicked(self) -> None:
        """Handle float button click - dock the widget back.

        We use QTimer.singleShot to defer the setFloating call. This is critical
        because setFloating(False) triggers topLevelChanged which causes
        setTitleBarWidget(None) to be called, which deletes this FloatingDockTitleBar.
        If we called setFloating synchronously, we'd be deleting ourselves while
        still executing this method, causing a crash.
        """
        dock_title = self._dock.windowTitle()
        _debug(f"FloatingDockTitleBar._on_float_clicked: dock={dock_title!r}")
        # Capture dock reference before potentially being deleted
        dock = self._dock
        # Defer to avoid deleting ourselves while in this method
        QTimer.singleShot(0, lambda: dock.setFloating(False))
        _debug("  -> setFloating(False) scheduled")

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start drag on left mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move the floating dock on drag."""
        if self._drag_start_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            self._dock.move(self._dock.pos() + delta)
            self._drag_start_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End drag on mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double-click - this is where maximize/restore happens.

        The actual behavior is controlled by the event filter on the dock widget,
        but we need to make sure the event reaches the dock. We call the parent
        class which will propagate the event.
        """
        # Let the event propagate - the dock's event filter will handle it
        super().mouseDoubleClickEvent(event)
