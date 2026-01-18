"""Tests for theme discovery and management."""

from pathlib import Path

from assertpy import assert_that

from qtpie.styles.themes import (
    Theme,
    ThemeMode,
    ThemeSet,
    detect_mode,
    find_scss_entry_point,
)

FIXTURES = Path(__file__).parent / "fixtures" / "themes"


class TestThemeModeDetection:
    """Tests for detect_mode function."""

    def test_dark_exact_match(self) -> None:
        """'dark' returns Dark mode."""
        assert_that(detect_mode("dark")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("Dark")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("DARK")).is_equal_to(ThemeMode.Dark)

    def test_light_exact_match(self) -> None:
        """'light' returns Light mode."""
        assert_that(detect_mode("light")).is_equal_to(ThemeMode.Light)
        assert_that(detect_mode("Light")).is_equal_to(ThemeMode.Light)
        assert_that(detect_mode("LIGHT")).is_equal_to(ThemeMode.Light)

    def test_suffix_dark(self) -> None:
        """'*-dark' suffix returns Dark mode."""
        assert_that(detect_mode("solarized-dark")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("catppuccin-dark")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("Gruvbox-Dark")).is_equal_to(ThemeMode.Dark)

    def test_suffix_light(self) -> None:
        """'*-light' suffix returns Light mode."""
        assert_that(detect_mode("solarized-light")).is_equal_to(ThemeMode.Light)
        assert_that(detect_mode("catppuccin-light")).is_equal_to(ThemeMode.Light)
        assert_that(detect_mode("Gruvbox-Light")).is_equal_to(ThemeMode.Light)

    def test_prefix_dark(self) -> None:
        """'dark-*' prefix returns Dark mode."""
        assert_that(detect_mode("dark-contrast")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("dark-high-contrast")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("Dark-Modern")).is_equal_to(ThemeMode.Dark)

    def test_prefix_light(self) -> None:
        """'light-*' prefix returns Light mode."""
        assert_that(detect_mode("light-contrast")).is_equal_to(ThemeMode.Light)
        assert_that(detect_mode("light-high-contrast")).is_equal_to(ThemeMode.Light)
        assert_that(detect_mode("Light-Modern")).is_equal_to(ThemeMode.Light)

    def test_unknown_defaults_to_dark(self) -> None:
        """Unknown theme names default to Dark mode."""
        assert_that(detect_mode("monokai")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("dracula")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("nord")).is_equal_to(ThemeMode.Dark)
        assert_that(detect_mode("catppuccin")).is_equal_to(ThemeMode.Dark)


class TestScssEntryPointDetection:
    """Tests for find_scss_entry_point function."""

    def test_finds_main_scss(self) -> None:
        """Finds main.scss as entry point."""
        entry = find_scss_entry_point(FIXTURES / "monokai")
        assert_that(entry).is_not_none()
        assert_that(entry.name).is_equal_to("main.scss")  # type: ignore[union-attr]

    def test_finds_theme_scss(self) -> None:
        """Finds theme.scss as entry point."""
        entry = find_scss_entry_point(FIXTURES / "nord-light")
        assert_that(entry).is_not_none()
        assert_that(entry.name).is_equal_to("theme.scss")  # type: ignore[union-attr]

    def test_ignores_underscore_prefixed(self) -> None:
        """Ignores _*.scss files (partials)."""
        # monokai has both main.scss and _colors.scss
        entry = find_scss_entry_point(FIXTURES / "monokai")
        assert_that(entry).is_not_none()
        assert_that(entry.name.startswith("_")).is_false()  # type: ignore[union-attr]

    def test_returns_none_for_empty_folder(self, tmp_path: Path) -> None:
        """Returns None if no entry point found."""
        entry = find_scss_entry_point(tmp_path)
        assert_that(entry).is_none()

    def test_returns_none_for_only_partials(self, tmp_path: Path) -> None:
        """Returns None if folder only contains partials."""
        (tmp_path / "_partial1.scss").write_text("// partial")
        (tmp_path / "_partial2.scss").write_text("// partial")

        entry = find_scss_entry_point(tmp_path)
        assert_that(entry).is_none()


class TestThemeDiscovery:
    """Tests for theme discovery from folder structure."""

    def test_discovers_qss_files(self) -> None:
        """Discovers QSS files as themes."""
        theme_set = ThemeSet(FIXTURES)

        assert_that(theme_set.themes).contains_key("dark")
        assert_that(theme_set.themes).contains_key("light")

        dark = theme_set.get_theme("dark")
        assert_that(dark).is_not_none()
        assert_that(dark.is_scss).is_false()  # type: ignore[union-attr]
        assert_that(dark.mode).is_equal_to(ThemeMode.Dark)  # type: ignore[union-attr]

        light = theme_set.get_theme("light")
        assert_that(light).is_not_none()
        assert_that(light.is_scss).is_false()  # type: ignore[union-attr]
        assert_that(light.mode).is_equal_to(ThemeMode.Light)  # type: ignore[union-attr]

    def test_discovers_scss_folders(self) -> None:
        """Discovers SCSS folders as themes."""
        theme_set = ThemeSet(FIXTURES)

        assert_that(theme_set.themes).contains_key("monokai")
        assert_that(theme_set.themes).contains_key("nord-light")

        monokai = theme_set.get_theme("monokai")
        assert_that(monokai).is_not_none()
        assert_that(monokai.is_scss).is_true()  # type: ignore[union-attr]
        assert_that(monokai.entry_point).is_not_none()  # type: ignore[union-attr]
        assert_that(monokai.mode).is_equal_to(ThemeMode.Dark)  # type: ignore[union-attr]

        nord_light = theme_set.get_theme("nord-light")
        assert_that(nord_light).is_not_none()
        assert_that(nord_light.is_scss).is_true()  # type: ignore[union-attr]
        assert_that(nord_light.mode).is_equal_to(ThemeMode.Light)  # type: ignore[union-attr]

    def test_mixed_qss_and_scss(self) -> None:
        """Discovers both QSS files and SCSS folders."""
        theme_set = ThemeSet(FIXTURES)

        # Should have both QSS and SCSS themes
        qss_themes = [t for t in theme_set.themes.values() if not t.is_scss]
        scss_themes = [t for t in theme_set.themes.values() if t.is_scss]

        assert_that(qss_themes).is_not_empty()
        assert_that(scss_themes).is_not_empty()

    def test_empty_folder(self, tmp_path: Path) -> None:
        """Empty folder returns no themes."""
        theme_set = ThemeSet(tmp_path)
        assert_that(theme_set.themes).is_empty()

    def test_nonexistent_folder(self, tmp_path: Path) -> None:
        """Nonexistent folder returns no themes."""
        theme_set = ThemeSet(tmp_path / "nonexistent")
        assert_that(theme_set.themes).is_empty()


class TestThemeSet:
    """Tests for ThemeSet class."""

    def test_theme_names_sorted(self) -> None:
        """theme_names returns sorted list."""
        theme_set = ThemeSet(FIXTURES)
        names = theme_set.theme_names

        assert_that(names).is_equal_to(sorted(names))

    def test_get_theme_by_name(self) -> None:
        """get_theme returns theme by name."""
        theme_set = ThemeSet(FIXTURES)

        dark = theme_set.get_theme("dark")
        assert_that(dark).is_not_none()
        assert_that(dark).is_instance_of(Theme)
        assert_that(dark.name).is_equal_to("dark")  # type: ignore[union-attr]

    def test_get_theme_returns_none_for_unknown(self) -> None:
        """get_theme returns None for unknown theme."""
        theme_set = ThemeSet(FIXTURES)

        result = theme_set.get_theme("nonexistent")
        assert_that(result).is_none()

    def test_set_theme(self) -> None:
        """set_theme sets current theme."""
        theme_set = ThemeSet(FIXTURES)

        assert_that(theme_set.current_theme).is_none()

        result = theme_set.set_theme("dark")
        assert_that(result).is_true()
        assert_that(theme_set.current_theme).is_not_none()
        assert_that(theme_set.current_theme_name).is_equal_to("dark")

    def test_set_theme_returns_false_for_unknown(self) -> None:
        """set_theme returns False for unknown theme."""
        theme_set = ThemeSet(FIXTURES)

        result = theme_set.set_theme("nonexistent")
        assert_that(result).is_false()
        assert_that(theme_set.current_theme).is_none()

    def test_current_theme_initially_none(self) -> None:
        """current_theme is None initially."""
        theme_set = ThemeSet(FIXTURES)
        assert_that(theme_set.current_theme).is_none()
        assert_that(theme_set.current_theme_name).is_none()

    def test_refresh_rescans_directory(self, tmp_path: Path) -> None:
        """refresh() re-scans the themes directory."""
        theme_set = ThemeSet(tmp_path)
        assert_that(theme_set.themes).is_empty()

        # Add a theme file
        (tmp_path / "custom.qss").write_text("/* custom */")

        theme_set.refresh()
        assert_that(theme_set.themes).contains_key("custom")

    def test_refresh_clears_missing_current_theme(self, tmp_path: Path) -> None:
        """refresh() clears current_theme if it no longer exists."""
        # Create initial theme
        qss_file = tmp_path / "temp.qss"
        qss_file.write_text("/* temp */")

        theme_set = ThemeSet(tmp_path)
        theme_set.set_theme("temp")
        assert_that(theme_set.current_theme_name).is_equal_to("temp")

        # Remove theme file and refresh
        qss_file.unlink()
        theme_set.refresh()

        assert_that(theme_set.current_theme).is_none()

    def test_is_qrc_false_for_filesystem(self) -> None:
        """is_qrc is False for filesystem paths."""
        theme_set = ThemeSet(FIXTURES)
        assert_that(theme_set.is_qrc).is_false()

    def test_is_qrc_true_for_qrc_path(self) -> None:
        """is_qrc is True for QRC paths."""
        theme_set = ThemeSet(":/themes")
        assert_that(theme_set.is_qrc).is_true()
