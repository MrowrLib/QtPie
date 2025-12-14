"""Tests for the regular Qt app sample."""

from assertpy import assert_that
from samples.regular_qt_app.app import MainWindow

from qtpie_test import QtDriver


class TestMainWindow:
    def test_window_title(self, qt: QtDriver) -> None:
        window = MainWindow()
        qt.track(window)

        assert_that(window.windowTitle()).is_equal_to("Regular Qt App")

    def test_initial_label_text(self, qt: QtDriver) -> None:
        window = MainWindow()
        qt.track(window)

        assert_that(window.label.text()).is_equal_to("Hello, World!")

    def test_button_click_updates_label(self, qt: QtDriver) -> None:
        window = MainWindow()
        qt.track(window)

        qt.click(window.button)

        assert_that(window.label.text()).is_equal_to("Clicked 1 time(s)")

    def test_multiple_button_clicks(self, qt: QtDriver) -> None:
        window = MainWindow()
        qt.track(window)

        qt.click(window.button)
        qt.click(window.button)
        qt.click(window.button)

        assert_that(window.label.text()).is_equal_to("Clicked 3 time(s)")
        assert_that(window.click_count).is_equal_to(3)
