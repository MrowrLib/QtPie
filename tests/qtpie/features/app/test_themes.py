# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportArgumentType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnknownVariableType=false
"""Tests for theme system integration.

These tests verify the theme runtime API and theme application
when used with real Qt widgets and applications.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from qtpie.styles import (
    get_theme,
    get_themes,
    is_dark_theme,
    set_theme,
)
from qtpie.styles.theme_runtime import cleanup_themes, init_themes
from qtpie.styles.themes import ThemeMode, ThemeSet
from qtpie.testing import QtDriver

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "themes"


class TestThemeRuntimeAPI:
    """Test global theme runtime API functions."""

    def test_get_themes_returns_empty_before_init(self, qt: QtDriver) -> None:
        """get_themes() returns empty list when not initialized."""
        cleanup_themes()
        themes = get_themes()
        assert_that(themes).is_empty()

    def test_get_theme_returns_none_before_init(self, qt: QtDriver) -> None:
        """get_theme() returns None when not initialized."""
        cleanup_themes()
        theme = get_theme()
        assert_that(theme).is_none()

    def test_is_dark_theme_returns_false_before_init(self, qt: QtDriver) -> None:
        """is_dark_theme() returns False when not initialized."""
        cleanup_themes()
        result = is_dark_theme()
        assert_that(result).is_false()

    def test_set_theme_returns_false_before_init(self, qt: QtDriver) -> None:
        """set_theme() returns False when not initialized."""
        cleanup_themes()
        result = set_theme("dark")
        assert_that(result).is_false()

    def test_init_themes_discovers_themes(self, qt: QtDriver, qapp) -> None:
        """init_themes() discovers themes from directory."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp)

        themes = get_themes()
        assert_that(themes).contains("dark", "light", "monokai", "nord-light")

    def test_get_theme_after_init_with_theme(self, qt: QtDriver, qapp) -> None:
        """get_theme() returns the initial theme name."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        assert_that(get_theme()).is_equal_to("dark")

    def test_set_theme_switches_theme(self, qt: QtDriver, qapp) -> None:
        """set_theme() switches to a different theme."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        result = set_theme("light")
        assert_that(result).is_true()
        assert_that(get_theme()).is_equal_to("light")

    def test_set_theme_returns_false_for_unknown(self, qt: QtDriver, qapp) -> None:
        """set_theme() returns False for unknown theme."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        result = set_theme("nonexistent")
        assert_that(result).is_false()
        assert_that(get_theme()).is_equal_to("dark")

    def test_is_dark_theme_for_dark_theme(self, qt: QtDriver, qapp) -> None:
        """is_dark_theme() returns True for dark themes."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        assert_that(is_dark_theme()).is_true()

    def test_is_dark_theme_for_light_theme(self, qt: QtDriver, qapp) -> None:
        """is_dark_theme() returns False for light themes."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="light")

        assert_that(is_dark_theme()).is_false()

    def test_is_dark_theme_for_nord_light(self, qt: QtDriver, qapp) -> None:
        """is_dark_theme() returns False for themes ending in -light."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="nord-light")

        assert_that(is_dark_theme()).is_false()

    def test_cleanup_themes_clears_state(self, qt: QtDriver, qapp) -> None:
        """cleanup_themes() clears all global state."""
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        cleanup_themes()

        assert_that(get_theme()).is_none()
        assert_that(get_themes()).is_empty()


class TestThemeApplication:
    """Test that themes are correctly applied to the application."""

    def test_qss_theme_applied_to_app(self, qt: QtDriver, qapp) -> None:
        """QSS theme stylesheet is applied to the application."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        # The dark.qss sets background-color: #1e1e1e
        stylesheet = qapp.styleSheet()
        assert_that(stylesheet).contains("background-color: #1e1e1e")

    def test_qss_theme_switch_updates_stylesheet(self, qt: QtDriver, qapp) -> None:
        """Switching themes updates the application stylesheet."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="dark")

        set_theme("light")

        # The light.qss sets background-color: #ffffff
        stylesheet = qapp.styleSheet()
        assert_that(stylesheet).contains("background-color: #ffffff")

    @pytest.mark.skipif(
        not FIXTURES_DIR.joinpath("monokai").exists(),
        reason="SCSS fixture not available",
    )
    def test_scss_theme_compiled_and_applied(self, qt: QtDriver, qapp) -> None:
        """SCSS theme is compiled and applied."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="monokai")

        # The monokai theme uses $bg: #272822 in _colors.scss
        stylesheet = qapp.styleSheet()
        assert_that(stylesheet).contains("background-color: #272822")

    @pytest.mark.skipif(
        not FIXTURES_DIR.joinpath("_shared").exists(),
        reason="Shared SCSS fixture not available",
    )
    def test_scss_shared_import_works(self, qt: QtDriver, qapp) -> None:
        """SCSS themes can import from shared folders in themes directory."""
        cleanup_themes()
        init_themes(FIXTURES_DIR, qapp, initial_theme="monokai")

        # The monokai theme imports _shared/_shared.scss which defines $shared-color: #ff00ff
        stylesheet = qapp.styleSheet()
        assert_that(stylesheet).contains("border-color: #ff00ff")


class TestThemeSet:
    """Test ThemeSet directly for edge cases."""

    def test_theme_set_current_theme_name(self) -> None:
        """current_theme_name returns the current theme name."""
        theme_set = ThemeSet(FIXTURES_DIR)
        theme_set.set_theme("dark")

        assert_that(theme_set.current_theme_name).is_equal_to("dark")

    def test_theme_set_current_theme_mode(self) -> None:
        """current_theme returns Theme with correct mode."""
        theme_set = ThemeSet(FIXTURES_DIR)
        theme_set.set_theme("dark")

        assert_that(theme_set.current_theme).is_not_none()
        assert_that(theme_set.current_theme.mode).is_equal_to(ThemeMode.Dark)

    def test_theme_set_get_theme(self) -> None:
        """get_theme() returns Theme by name."""
        theme_set = ThemeSet(FIXTURES_DIR)

        dark_theme = theme_set.get_theme("dark")
        assert_that(dark_theme).is_not_none()
        assert_that(dark_theme.name).is_equal_to("dark")

    def test_theme_set_get_nonexistent_theme(self) -> None:
        """get_theme() returns None for nonexistent theme."""
        theme_set = ThemeSet(FIXTURES_DIR)

        theme = theme_set.get_theme("nonexistent")
        assert_that(theme).is_none()
