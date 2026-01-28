# pyright: reportPrivateUsage=false
"""Tests for screen utilities."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel

from qtpie.screen import center_on_screen
from qtpie.testing import QtDriver


class TestCenterOnScreen:
    """Test center_on_screen() utility function."""

    def test_center_on_screen_moves_widget(self, qt: QtDriver) -> None:
        """center_on_screen() moves widget to center of screen."""
        label = qt.track(QLabel("Test"))
        label.resize(200, 100)

        # Move to corner first
        label.move(0, 0)

        # Center it
        center_on_screen(label)

        # Verify it moved (exact position depends on screen)
        screen = label.screen()
        screen_geo = screen.availableGeometry()
        expected_x = screen_geo.x() + (screen_geo.width() - 200) // 2
        expected_y = screen_geo.y() + (screen_geo.height() - 100) // 2

        assert_that(label.x()).is_equal_to(expected_x)
        assert_that(label.y()).is_equal_to(expected_y)
