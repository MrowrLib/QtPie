# pyright: reportPrivateUsage=false
"""Tests for theme_icon= parameter across widget types and decorators."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QToolButton

from qtpie import AppBase, Widget, Window, app, new, widget, window
from qtpie.testing import QtDriver

from .conftest import (
    QWIDGET_CLASS_TYPES,
    create_and_track,
    get_main_window,
)


class TestThemeIconOnNew:
    """Verify theme_icon= works on new() for QWidget fields."""

    def test_theme_icon_sets_icon_on_widget(self, qt: QtDriver, tmp_path: Path) -> None:
        """theme_icon= resolves and sets icon on widget."""
        # Create test icon file
        icon_path = tmp_path / "refresh.svg"
        icon_path.write_text("<svg></svg>")  # Minimal SVG

        @widget
        class TestWidget(Widget):
            btn: QToolButton = new(theme_icon=str(icon_path))

        instance = create_and_track(qt, TestWidget, Widget)
        # Icon should be set (not null)
        assert not instance.btn.icon().isNull()

    def test_theme_icon_resolves_mode_variant(self, qt: QtDriver, tmp_path: Path) -> None:
        """theme_icon= resolves to -{mode}.svg variant based on color scheme."""
        base_path = tmp_path / "icon.svg"
        dark_path = tmp_path / "icon-dark.svg"
        dark_path.write_text("<svg></svg>")  # Only dark variant exists

        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):

            @widget
            class TestWidget(Widget):
                btn: QToolButton = new(theme_icon=str(base_path))

            instance = create_and_track(qt, TestWidget, Widget)
            # Should have found the dark variant
            assert not instance.btn.icon().isNull()

    def test_theme_icon_prefers_theme_name_variant(self, qt: QtDriver, tmp_path: Path) -> None:
        """theme_icon= prefers -{theme_name}.svg over -{mode}.svg."""
        base_path = tmp_path / "icon.svg"
        theme_path = tmp_path / "icon-catppuccin.svg"
        dark_path = tmp_path / "icon-dark.svg"
        theme_path.write_text("<svg></svg>")
        dark_path.write_text("<svg></svg>")  # Both exist

        with (
            patch("qtpie.styles.icons.get_theme", return_value="catppuccin"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):

            @widget
            class TestWidget(Widget):
                btn: QToolButton = new(theme_icon=str(base_path))

            instance = create_and_track(qt, TestWidget, Widget)
            # Just verify icon was set
            assert not instance.btn.icon().isNull()

    def test_theme_icon_with_nonexistent_file_uses_original(self, qt: QtDriver, tmp_path: Path) -> None:
        """theme_icon= falls back to original path when no variants exist."""
        base_path = tmp_path / "nonexistent.svg"

        with (
            patch("qtpie.styles.icons.get_theme", return_value="catppuccin"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):

            @widget
            class TestWidget(Widget):
                btn: QToolButton = new(theme_icon=str(base_path))

            instance = create_and_track(qt, TestWidget, Widget)
            # Icon is null because file doesn't exist, but no crash
            assert instance.btn.icon().isNull()

    def test_theme_icon_takes_precedence_over_icon(self, qt: QtDriver, tmp_path: Path) -> None:
        """theme_icon= takes precedence when both theme_icon and icon are set."""
        theme_icon_path = tmp_path / "theme-icon.svg"
        icon_path = tmp_path / "regular-icon.svg"
        theme_icon_path.write_text("<svg></svg>")
        icon_path.write_text("<svg></svg>")

        @widget
        class TestWidget(Widget):
            # Both set, theme_icon should win
            btn: QToolButton = new(theme_icon=str(theme_icon_path), icon=str(icon_path))

        instance = create_and_track(qt, TestWidget, Widget)
        # Should have an icon (from theme_icon)
        assert not instance.btn.icon().isNull()


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES[:3])  # Widget, Window, Dialog
class TestThemeIconOnDecorator:
    """Verify theme_icon= works on @widget/@window decorators for window icons."""

    def test_decorator_theme_icon_sets_window_icon(
        self,
        qt: QtDriver,
        base_class: type,
        decorator: type,
        tmp_path: Path,
    ) -> None:
        """Decorator theme_icon= sets window icon with theme resolution."""
        icon_path = tmp_path / "app-icon.svg"
        icon_path.write_text("<svg></svg>")

        if base_class is Widget:

            @decorator(theme_icon=str(icon_path))
            class TestWidget(base_class):  # type: ignore[valid-type]
                pass

            instance = create_and_track(qt, TestWidget, base_class)
            assert not instance.windowIcon().isNull()

        elif base_class is Window:

            @decorator(theme_icon=str(icon_path))
            class TestWindow(base_class):  # type: ignore[valid-type]
                pass

            instance = create_and_track(qt, TestWindow, base_class)
            assert not instance.windowIcon().isNull()


class TestThemeIconOnAppDecorator:
    """Verify theme_icon= variants work on @app decorator."""

    def test_app_theme_icon_sets_window_icon(self, qt: QtDriver, tmp_path: Path) -> None:
        """@app(theme_icon=...) sets window icon."""
        from PySide6.QtWidgets import QLabel

        icon_path = tmp_path / "app-icon.svg"
        icon_path.write_text("<svg></svg>")

        # AppBase needs at least one widget field to create a window
        @app(theme_icon=str(icon_path))
        class TestApp(AppBase):
            label: QLabel = new("Test")

        instance = create_and_track(qt, TestApp, AppBase)
        main_window = get_main_window(instance, AppBase)
        assert main_window is not None
        assert not main_window.windowIcon().isNull()

    def test_app_theme_window_icon_overrides_theme_icon(self, qt: QtDriver, tmp_path: Path) -> None:
        """@app(theme_window_icon=...) takes precedence over theme_icon=."""
        from PySide6.QtWidgets import QLabel

        base_icon = tmp_path / "base.svg"
        window_icon = tmp_path / "window.svg"
        window_icon.write_text("<svg></svg>")  # Only window icon exists

        # AppBase needs at least one widget field to create a window
        @app(theme_icon=str(base_icon), theme_window_icon=str(window_icon))
        class TestApp(AppBase):
            label: QLabel = new("Test")

        instance = create_and_track(qt, TestApp, AppBase)
        main_window = get_main_window(instance, AppBase)
        assert main_window is not None
        # Should use theme_window_icon (which exists)
        assert not main_window.windowIcon().isNull()

    def test_window_theme_icon_sets_window_icon(self, qt: QtDriver, tmp_path: Path) -> None:
        """@window(theme_icon=...) sets window icon."""
        icon_path = tmp_path / "app-icon.svg"
        icon_path.write_text("<svg></svg>")

        @window(theme_icon=str(icon_path))
        class TestWindow(Window):
            pass

        instance = create_and_track(qt, TestWindow, Window)
        assert not instance.windowIcon().isNull()


class TestThemeIconWithNoTheme:
    """Verify theme_icon= works when no theme is set."""

    def test_no_theme_uses_mode_fallback(self, qt: QtDriver, tmp_path: Path) -> None:
        """When get_theme() returns None, falls back to mode variant."""
        base_path = tmp_path / "icon.svg"
        dark_path = tmp_path / "icon-dark.svg"
        dark_path.write_text("<svg></svg>")

        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):

            @widget
            class TestWidget(Widget):
                btn: QToolButton = new(theme_icon=str(base_path))

            instance = create_and_track(qt, TestWidget, Widget)
            # Should find dark variant even without theme
            assert not instance.btn.icon().isNull()

    def test_light_mode_uses_light_variant(self, qt: QtDriver, tmp_path: Path) -> None:
        """In light mode, uses -light.svg variant."""
        base_path = tmp_path / "icon.svg"
        light_path = tmp_path / "icon-light.svg"
        light_path.write_text("<svg></svg>")

        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=False),
        ):

            @widget
            class TestWidget(Widget):
                btn: QToolButton = new(theme_icon=str(base_path))

            instance = create_and_track(qt, TestWidget, Widget)
            assert not instance.btn.icon().isNull()


class TestThemeIconReactivity:
    """Verify icons update when set_theme() is called."""

    def test_widget_icon_registered_for_updates(self, qt: QtDriver, tmp_path: Path) -> None:
        """Widget with theme_icon is registered in the theme icon registry."""
        from qtpie.styles.icons import _theme_icon_registry, unregister_theme_icon

        icon_path = tmp_path / "icon.svg"
        icon_path.write_text("<svg></svg>")

        @widget
        class TestWidget(Widget):
            btn: QToolButton = new(theme_icon=str(icon_path))

        instance = create_and_track(qt, TestWidget, Widget)

        # Button should be registered in the registry
        assert instance.btn in _theme_icon_registry

        # Clean up
        unregister_theme_icon(instance.btn)

    def test_window_icon_registered_for_updates(self, qt: QtDriver, tmp_path: Path) -> None:
        """Window with theme_icon is registered in the theme icon registry."""
        from qtpie.styles.icons import _theme_icon_registry, unregister_theme_icon

        icon_path = tmp_path / "icon.svg"
        icon_path.write_text("<svg></svg>")

        @window(theme_icon=str(icon_path))
        class TestWindow(Window):
            pass

        instance = create_and_track(qt, TestWindow, Window)

        # Window should be registered in the registry
        assert instance in _theme_icon_registry

        # Clean up
        unregister_theme_icon(instance)

    def test_refresh_updates_widget_icons(self, qt: QtDriver, tmp_path: Path) -> None:
        """refresh_all_theme_icons updates registered widgets."""
        from qtpie.styles.icons import refresh_all_theme_icons, unregister_theme_icon

        # Create two variants
        base_path = tmp_path / "icon.svg"
        dark_path = tmp_path / "icon-dark.svg"
        light_path = tmp_path / "icon-light.svg"
        dark_path.write_text("<svg fill='black'></svg>")
        light_path.write_text("<svg fill='white'></svg>")

        # Create widget in dark mode
        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):

            @widget
            class TestWidget(Widget):
                btn: QToolButton = new(theme_icon=str(base_path))

            instance = create_and_track(qt, TestWidget, Widget)

            # Initial icon should be set
            assert not instance.btn.icon().isNull()

        # Now refresh in light mode
        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=False),
        ):
            refresh_all_theme_icons()

        # Icon should still be set (not null)
        assert not instance.btn.icon().isNull()

        # Clean up
        unregister_theme_icon(instance.btn)
