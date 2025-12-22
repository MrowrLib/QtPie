"""Tests for Widget base class functionality."""

from pathlib import Path

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie import Widget, widget
from qtpie_test import QtDriver


class TestWidgetLoadStylesheet:
    """Tests for Widget.load_stylesheet() method."""

    def test_widget_has_load_stylesheet_method(self, qt: QtDriver) -> None:
        """Widget subclass should have a load_stylesheet method."""

        @widget()
        class TestWidget(QWidget, Widget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(w.load_stylesheet).is_not_none()
        assert_that(callable(w.load_stylesheet)).is_true()

    def test_widget_load_stylesheet_from_file(self, qt: QtDriver, tmp_path: Path) -> None:
        """Widget should be able to load a stylesheet from a file."""

        @widget()
        class TestWidget(QWidget, Widget):
            pass

        qss_file = tmp_path / "test.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        w = TestWidget()
        qt.track(w)

        w.load_stylesheet(str(qss_file))

        assert_that(w.styleSheet()).contains("background-color")

    def test_widget_load_stylesheet_nonexistent_file(self, qt: QtDriver) -> None:
        """Widget should handle nonexistent stylesheet gracefully."""

        @widget()
        class TestWidget(QWidget, Widget):
            pass

        w = TestWidget()
        qt.track(w)

        # Should not raise
        w.load_stylesheet("/nonexistent/path/style.qss")
        # Stylesheet might be empty but shouldn't crash
