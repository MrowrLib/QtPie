# pyright: reportPrivateUsage=false
"""Tests for theme-aware icon resolution."""

from pathlib import Path
from unittest.mock import patch

from qtpie.styles.icons import _split_path, resolve_theme_icon


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
