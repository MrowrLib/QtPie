"""Tests for color scheme helpers."""

from __future__ import annotations

import os
from unittest.mock import patch

from assertpy import assert_that
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication

from qtpie.styles import (
    ColorScheme,
    enable_dark_mode,
    enable_light_mode,
    set_color_scheme,
)


class TestSetColorSchemeWithApp:
    """Tests for set_color_scheme when an app exists."""

    def test_set_dark_mode_on_existing_app(self, qapp: QApplication) -> None:
        """Sets dark color scheme via Qt API when app exists."""
        set_color_scheme(ColorScheme.Dark)

        assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)

    def test_set_light_mode_on_existing_app(self, qapp: QApplication) -> None:
        """Sets light color scheme via Qt API when app exists."""
        set_color_scheme(ColorScheme.Light)

        assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Light)

    def test_set_color_scheme_with_explicit_app(self, qapp: QApplication) -> None:
        """Accepts explicit app parameter."""
        set_color_scheme(ColorScheme.Dark, qapp)

        assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)


class TestSetColorSchemeWithoutApp:
    """Tests for set_color_scheme when no app exists (uses env vars)."""

    def test_set_dark_mode_sets_env_var(self) -> None:
        """Sets QT_QPA_PLATFORM env var for dark mode when no app exists."""
        with patch.object(QApplication, "instance", return_value=None):
            # Clear any existing value
            os.environ.pop("QT_QPA_PLATFORM", None)

            set_color_scheme(ColorScheme.Dark)

            assert_that(os.environ.get("QT_QPA_PLATFORM")).is_equal_to("windows:darkmode=2")

    def test_set_light_mode_sets_env_var(self) -> None:
        """Sets QT_QPA_PLATFORM env var for light mode when no app exists."""
        with patch.object(QApplication, "instance", return_value=None):
            # Clear any existing value
            os.environ.pop("QT_QPA_PLATFORM", None)

            set_color_scheme(ColorScheme.Light)

            assert_that(os.environ.get("QT_QPA_PLATFORM")).is_equal_to("windows:darkmode=0")


class TestEnableDarkMode:
    """Tests for enable_dark_mode helper."""

    def test_enable_dark_mode_with_app(self, qapp: QApplication) -> None:
        """Enables dark mode via Qt API when app exists."""
        enable_dark_mode()

        assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)

    def test_enable_dark_mode_without_app(self) -> None:
        """Sets env var when no app exists."""
        with patch.object(QApplication, "instance", return_value=None):
            os.environ.pop("QT_QPA_PLATFORM", None)

            enable_dark_mode()

            assert_that(os.environ.get("QT_QPA_PLATFORM")).is_equal_to("windows:darkmode=2")


class TestEnableLightMode:
    """Tests for enable_light_mode helper."""

    def test_enable_light_mode_with_app(self, qapp: QApplication) -> None:
        """Enables light mode via Qt API when app exists."""
        enable_light_mode()

        assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Light)

    def test_enable_light_mode_without_app(self) -> None:
        """Sets env var when no app exists."""
        with patch.object(QApplication, "instance", return_value=None):
            os.environ.pop("QT_QPA_PLATFORM", None)

            enable_light_mode()

            assert_that(os.environ.get("QT_QPA_PLATFORM")).is_equal_to("windows:darkmode=0")
