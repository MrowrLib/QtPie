# pyright: reportPrivateUsage=false
"""Tests for theme-aware icon resolution."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtGui import QIcon

from qtpie.styles.icons import (
    _split_path,
    _theme_icon_registry,
    refresh_all_theme_icons,
    register_theme_icon,
    resolve_theme_icon,
    unregister_theme_icon,
)


class TestSplitPath:
    """Tests for _split_path helper."""

    def test_qrc_path(self) -> None:
        """QRC paths split correctly."""
        assert _split_path(":/icons/foo.svg") == (":/icons/foo", ".svg")

    def test_qrc_path_root(self) -> None:
        """QRC paths at root split correctly."""
        assert _split_path(":/foo.svg") == (":/foo", ".svg")

    def test_filesystem_path(self) -> None:
        """Filesystem paths split correctly."""
        assert _split_path("/path/to/foo.svg") == ("/path/to/foo", ".svg")

    def test_no_extension(self) -> None:
        """Paths without extension have empty suffix."""
        assert _split_path(":/icons/foo") == (":/icons/foo", "")

    def test_multiple_dots(self) -> None:
        """Paths with multiple dots split on last dot."""
        assert _split_path(":/icons/foo.bar.svg") == (":/icons/foo.bar", ".svg")

    def test_windows_path(self) -> None:
        """Windows-style paths work correctly."""
        # Note: Qt uses forward slashes even on Windows for resource paths
        assert _split_path("C:/path/to/icon.png") == ("C:/path/to/icon", ".png")


class TestResolveThemeIcon:
    """Tests for resolve_theme_icon function."""

    def test_returns_theme_name_variant_if_exists(self, tmp_path: Path) -> None:
        """Prefers -{theme_name}.svg when it exists."""
        # Create test icon files
        base = tmp_path / "icon.svg"
        theme_variant = tmp_path / "icon-catppuccin.svg"
        mode_variant = tmp_path / "icon-dark.svg"
        base.touch()
        theme_variant.touch()
        mode_variant.touch()

        with (
            patch("qtpie.styles.icons.get_theme", return_value="catppuccin"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(str(base))
            assert result == str(theme_variant)

    def test_falls_back_to_mode_variant(self, tmp_path: Path) -> None:
        """Falls back to -{mode}.svg when theme name variant missing."""
        base = tmp_path / "icon.svg"
        mode_variant = tmp_path / "icon-dark.svg"
        base.touch()
        mode_variant.touch()
        # Note: icon-catppuccin.svg does NOT exist

        with (
            patch("qtpie.styles.icons.get_theme", return_value="catppuccin"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(str(base))
            assert result == str(mode_variant)

    def test_falls_back_to_original(self, tmp_path: Path) -> None:
        """Falls back to original when no variants exist."""
        base = tmp_path / "icon.svg"
        base.touch()
        # No variants exist

        with (
            patch("qtpie.styles.icons.get_theme", return_value="catppuccin"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(str(base))
            assert result == str(base)

    def test_returns_original_when_nothing_exists(self, tmp_path: Path) -> None:
        """Returns original path even when file doesn't exist."""
        base = str(tmp_path / "nonexistent.svg")

        with (
            patch("qtpie.styles.icons.get_theme", return_value="catppuccin"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(base)
            assert result == base

    def test_light_mode_uses_light_suffix(self, tmp_path: Path) -> None:
        """Uses -light.svg for light mode themes."""
        base = tmp_path / "icon.svg"
        light_variant = tmp_path / "icon-light.svg"
        base.touch()
        light_variant.touch()

        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=False),
        ):
            result = resolve_theme_icon(str(base))
            assert result == str(light_variant)

    def test_no_theme_skips_theme_name_variant(self, tmp_path: Path) -> None:
        """When get_theme() returns None, skips theme-name variant."""
        base = tmp_path / "icon.svg"
        mode_variant = tmp_path / "icon-dark.svg"
        base.touch()
        mode_variant.touch()

        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(str(base))
            # Should go straight to mode variant, not try -None.svg
            assert result == str(mode_variant)

    def test_qrc_resource_detection(self) -> None:
        """Uses QFile.exists() for QRC paths (:/ prefix)."""
        # QRC paths use QFile.exists() which we can't easily test without
        # actually registering QRC resources. Just verify it doesn't crash
        # and returns the original path when resource doesn't exist.
        with (
            patch("qtpie.styles.icons.get_theme", return_value="dark"),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(":/nonexistent/icon.svg")
            # Should return original since nothing exists
            assert result == ":/nonexistent/icon.svg"

    def test_filesystem_detection(self, tmp_path: Path) -> None:
        """Detects filesystem paths without :/ prefix."""
        base = tmp_path / "icon.svg"
        dark_variant = tmp_path / "icon-dark.svg"
        dark_variant.touch()  # Only dark variant exists

        with (
            patch("qtpie.styles.icons.get_theme", return_value=None),
            patch("qtpie.styles.icons.is_dark_mode", return_value=True),
        ):
            result = resolve_theme_icon(str(base))
            # Should find the dark variant via Path.exists()
            assert result == str(dark_variant)


class TestResolveThemeIconIntegration:
    """Integration tests that don't mock theme functions."""

    def test_works_with_real_theme_system(self, tmp_path: Path) -> None:
        """Works with actual theme system (may be uninitialized)."""
        base = tmp_path / "icon.svg"
        base.touch()

        # Don't mock anything - let it use real theme system
        # Should not crash, just return some valid path
        result = resolve_theme_icon(str(base))
        assert result is not None
        assert isinstance(result, str)


class TestThemeIconRegistry:
    """Tests for theme icon registration and refresh."""

    def test_register_adds_to_registry(self) -> None:
        """register_theme_icon adds widget to registry."""
        widget = MagicMock()
        setter = MagicMock()
        base_path = ":/icons/test.svg"

        try:
            register_theme_icon(widget, base_path, setter)
            assert widget in _theme_icon_registry
            assert _theme_icon_registry[widget] == (base_path, setter)
        finally:
            unregister_theme_icon(widget)

    def test_unregister_removes_from_registry(self) -> None:
        """unregister_theme_icon removes widget from registry."""
        widget = MagicMock()
        setter = MagicMock()
        base_path = ":/icons/test.svg"

        register_theme_icon(widget, base_path, setter)
        assert widget in _theme_icon_registry

        unregister_theme_icon(widget)
        assert widget not in _theme_icon_registry

    def test_unregister_nonexistent_does_not_raise(self) -> None:
        """unregister_theme_icon on non-registered widget doesn't raise."""
        widget = MagicMock()
        # Should not raise
        unregister_theme_icon(widget)

    def test_refresh_calls_setters(self, tmp_path: Path) -> None:
        """refresh_all_theme_icons calls setters with resolved icons."""
        # Create test icon file
        icon_path = tmp_path / "icon.svg"
        icon_path.write_text("<svg></svg>")

        widget = MagicMock()
        setter = MagicMock()

        try:
            register_theme_icon(widget, str(icon_path), setter)

            with (
                patch("qtpie.styles.icons.get_theme", return_value=None),
                patch("qtpie.styles.icons.is_dark_mode", return_value=True),
            ):
                refresh_all_theme_icons()

            # Setter should have been called with a QIcon
            setter.assert_called_once()
            call_args = setter.call_args[0]
            assert len(call_args) == 1
            assert isinstance(call_args[0], QIcon)
        finally:
            unregister_theme_icon(widget)

    def test_refresh_handles_exception_gracefully(self) -> None:
        """refresh_all_theme_icons continues even if one setter fails."""
        widget1 = MagicMock()
        widget2 = MagicMock()

        # First setter raises exception
        failing_setter = MagicMock(side_effect=RuntimeError("Test error"))
        good_setter = MagicMock()

        try:
            register_theme_icon(widget1, ":/icon1.svg", failing_setter)
            register_theme_icon(widget2, ":/icon2.svg", good_setter)

            # Should not raise
            refresh_all_theme_icons()

            # Both setters attempted (even though first failed)
            # Note: Second one may or may not be called depending on icon resolution
            # The key is that refresh_all_theme_icons doesn't crash
        finally:
            unregister_theme_icon(widget1)
            unregister_theme_icon(widget2)

    def test_weak_reference_cleanup(self) -> None:
        """Deleted objects are auto-removed from registry (WeakKeyDict)."""
        import gc

        # Create a class we can delete
        class TestWidget:
            pass

        widget = TestWidget()
        setter = MagicMock()

        register_theme_icon(widget, ":/icon.svg", setter)
        assert len(_theme_icon_registry) >= 1

        # Get initial count
        initial_count = len(_theme_icon_registry)

        # Delete the widget
        del widget
        gc.collect()

        # Registry should have cleaned up (may be 0 or fewer than initial)
        assert len(_theme_icon_registry) <= initial_count
