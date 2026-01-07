"""Tests for the @entrypoint decorator."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QWidget

from qtpie import App, Widget, entrypoint, new, widget
from qtpie.entrypoint import (
    ENTRY_CONFIG_ATTR,
    EntryConfig,
    _apply_stylesheet,  # pyright: ignore[reportPrivateUsage]
    _compile_scss_to_string,  # pyright: ignore[reportPrivateUsage]
    _is_main_module,  # pyright: ignore[reportPrivateUsage]
    _load_qrc_stylesheet,  # pyright: ignore[reportPrivateUsage]
    _should_auto_run,  # pyright: ignore[reportPrivateUsage]
)


class TestHelperFunctions:
    """Tests for entrypoint helper functions (no qapp needed)."""

    def test_is_main_module_returns_true_for_main(self) -> None:
        """_is_main_module should return True when module is __main__."""

        def dummy() -> None:
            pass

        dummy.__module__ = "__main__"
        assert_that(_is_main_module(dummy)).is_true()

    def test_is_main_module_returns_false_for_other_module(self) -> None:
        """_is_main_module should return False for non-main modules."""

        def dummy() -> None:
            pass

        dummy.__module__ = "myapp.main"
        assert_that(_is_main_module(dummy)).is_false()

    def test_is_main_module_with_class(self) -> None:
        """_is_main_module should work with classes too."""

        class DummyClass:
            pass

        DummyClass.__module__ = "__main__"
        assert_that(_is_main_module(DummyClass)).is_true()

        DummyClass.__module__ = "some.module"
        assert_that(_is_main_module(DummyClass)).is_false()


class TestEntryConfig:
    """Tests for EntryConfig dataclass."""

    def test_entry_config_defaults(self) -> None:
        """EntryConfig should have sensible defaults."""
        config = EntryConfig()
        assert_that(config.dark_mode).is_false()
        assert_that(config.light_mode).is_false()
        assert_that(config.title).is_none()
        assert_that(config.size).is_none()
        assert_that(config.stylesheet).is_none()
        assert_that(config.watch_stylesheet).is_false()
        assert_that(config.scss_search_paths).is_equal_to(())
        assert_that(config.window).is_none()

    def test_entry_config_custom_values(self) -> None:
        """EntryConfig should accept custom values."""
        config = EntryConfig(
            dark_mode=True,
            title="My App",
            size=(800, 600),
        )
        assert_that(config.dark_mode).is_true()
        assert_that(config.title).is_equal_to("My App")
        assert_that(config.size).is_equal_to((800, 600))

    def test_entry_config_stylesheet_values(self) -> None:
        """EntryConfig should accept stylesheet-related values."""
        config = EntryConfig(
            stylesheet="styles.qss",
            watch_stylesheet=True,
            scss_search_paths=("path1", "path2"),
        )
        assert_that(config.stylesheet).is_equal_to("styles.qss")
        assert_that(config.watch_stylesheet).is_true()
        assert_that(config.scss_search_paths).is_equal_to(("path1", "path2"))


class TestEntryPointDecorator:
    """Tests for @entrypoint decorator behavior."""

    def test_entrypoint_stores_config_on_function(self) -> None:
        """@entrypoint should store config on decorated function."""

        @entrypoint(dark_mode=True, title="Test App")
        def my_main() -> QLabel:
            return QLabel("Hi")

        assert_that(hasattr(my_main, ENTRY_CONFIG_ATTR)).is_true()
        config = getattr(my_main, ENTRY_CONFIG_ATTR)
        assert_that(config.dark_mode).is_true()
        assert_that(config.title).is_equal_to("Test App")

    def test_entrypoint_stores_config_on_class(self) -> None:
        """@entrypoint should store config on decorated class."""

        @entrypoint(dark_mode=True, size=(1024, 768))
        @widget
        class TestWidget(Widget):
            label: QLabel = new("Test")

        assert_that(hasattr(TestWidget, ENTRY_CONFIG_ATTR)).is_true()
        config = getattr(TestWidget, ENTRY_CONFIG_ATTR)
        assert_that(config.dark_mode).is_true()
        assert_that(config.size).is_equal_to((1024, 768))

    def test_entrypoint_without_parens(self) -> None:
        """@entrypoint should work without parentheses."""

        @entrypoint
        def my_main() -> QLabel:
            return QLabel("Hi")

        assert_that(hasattr(my_main, ENTRY_CONFIG_ATTR)).is_true()
        config = getattr(my_main, ENTRY_CONFIG_ATTR)
        # Should have default values
        assert_that(config.dark_mode).is_false()
        assert_that(config.title).is_none()

    def test_entrypoint_preserves_function(self) -> None:
        """@entrypoint should preserve the original function."""

        @entrypoint
        def my_main() -> str:
            return "hello"

        # Function should still be callable and work
        assert_that(callable(my_main)).is_true()
        assert_that(my_main()).is_equal_to("hello")

    def test_entrypoint_preserves_class(self) -> None:
        """@entrypoint should preserve the original class."""

        @entrypoint
        @widget
        class TestWidget(Widget):
            label: QLabel = new("Test")

        # Class should still be instantiable
        w = TestWidget()
        assert_that(w).is_instance_of(QWidget)
        assert_that(w.label.text()).is_equal_to("Test")


class TestEntryPointWithQApp:
    """Tests for @entrypoint when QApplication exists."""

    def test_entrypoint_does_not_run_when_app_exists(self, qapp: App) -> None:
        """@entrypoint should not auto-run when QApplication exists."""
        run_count = 0

        @entrypoint
        def my_main() -> QLabel:
            nonlocal run_count
            run_count += 1
            return QLabel("Hi")

        # The decorator should not have run the function
        # because QApplication already exists (via qapp fixture)
        assert_that(run_count).is_equal_to(0)
        # Verify function is still callable
        assert_that(callable(my_main)).is_true()

    def test_should_auto_run_returns_false_when_app_exists(self, qapp: App) -> None:
        """_should_auto_run should return False when QApplication exists."""

        def dummy() -> None:
            pass

        dummy.__module__ = "__main__"

        # Even with __main__ module, should return False because app exists
        assert_that(_should_auto_run(dummy)).is_false()

    def test_widget_class_still_usable_with_entrypoint(self, qapp: App) -> None:
        """Widget class with @entrypoint should still be usable."""

        @entrypoint
        @widget
        class TestWidget(Widget):
            label: QLabel = new("Hello!")

        # Should be able to instantiate and use the widget
        w = TestWidget()
        assert_that(w.label.text()).is_equal_to("Hello!")


class TestLoadQrcStylesheet:
    """Tests for _load_qrc_stylesheet helper."""

    def test_loads_qrc_content(self) -> None:
        """Loads content from QRC path when file opens successfully."""
        mock_file = MagicMock()
        mock_file.open.return_value = True

        mock_stream = MagicMock()
        mock_stream.readAll.return_value = "QPushButton { color: red; }"

        with (
            patch("qtpie.entrypoint.QFile", return_value=mock_file),
            patch("qtpie.entrypoint.QTextStream", return_value=mock_stream),
        ):
            result = _load_qrc_stylesheet(":/styles/test.qss")

        assert_that(result).contains("QPushButton")
        assert_that(result).contains("color: red")

    def test_returns_empty_for_missing_qrc(self) -> None:
        """Returns empty string when QRC file doesn't exist."""
        mock_file = MagicMock()
        mock_file.open.return_value = False

        with patch("qtpie.entrypoint.QFile", return_value=mock_file):
            result = _load_qrc_stylesheet(":/nonexistent/styles.qss")

        assert_that(result).is_equal_to("")


class TestCompileScssToString:
    """Tests for _compile_scss_to_string helper."""

    def test_returns_empty_for_nonexistent_file(self) -> None:
        """Returns empty string when SCSS file doesn't exist."""
        result = _compile_scss_to_string("/nonexistent/file.scss", [])
        assert_that(result).is_equal_to("")

    def test_compiles_scss_file(self, tmp_path: Path) -> None:
        """Compiles SCSS file to CSS string."""
        scss_file = tmp_path / "test.scss"
        scss_file.write_text("$color: blue; QWidget { background: $color; }")

        result = _compile_scss_to_string(str(scss_file), [str(tmp_path)])

        assert_that(result).contains("background")
        assert_that(result).contains("blue")


class TestApplyStylesheet:
    """Tests for _apply_stylesheet helper."""

    def test_returns_none_when_no_stylesheet(self, qapp: App) -> None:
        """Returns None when stylesheet is not configured."""
        config = EntryConfig()
        result = _apply_stylesheet(qapp, config)
        assert_that(result).is_none()

    def test_loads_qss_file(self, qapp: App, tmp_path: Path) -> None:
        """Loads and applies QSS file."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: green; }")

        config = EntryConfig(stylesheet=str(qss_file))
        result = _apply_stylesheet(qapp, config)

        assert_that(result).is_none()
        assert_that(qapp.styleSheet()).contains("background-color: green")

    def test_returns_empty_for_missing_qss(self, qapp: App) -> None:
        """Returns None and doesn't crash when QSS file doesn't exist."""
        # Clear any existing stylesheet from previous tests
        qapp.setStyleSheet("")

        config = EntryConfig(stylesheet="/nonexistent/styles.qss")
        result = _apply_stylesheet(qapp, config)

        assert_that(result).is_none()
        # Stylesheet should remain empty (not set)
        assert_that(qapp.styleSheet()).is_equal_to("")

    def test_compiles_and_applies_scss(self, qapp: App, tmp_path: Path) -> None:
        """Compiles SCSS and applies it."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("$color: purple; QWidget { color: $color; }")

        config = EntryConfig(stylesheet=str(scss_file))
        result = _apply_stylesheet(qapp, config)

        assert_that(result).is_none()
        assert_that(qapp.styleSheet()).contains("purple")

    def test_returns_watcher_when_watch_qss_enabled(self, qapp: App, tmp_path: Path) -> None:
        """Returns QssWatcher when watch_stylesheet=True for QSS file."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: red; }")

        config = EntryConfig(stylesheet=str(qss_file), watch_stylesheet=True)
        watcher = _apply_stylesheet(qapp, config)

        assert_that(watcher).is_not_none()
        assert_that(type(watcher).__name__).is_equal_to("QssWatcher")
        watcher.stop()  # type: ignore[union-attr]

    def test_returns_scss_watcher_when_watch_scss_enabled(self, qapp: App, tmp_path: Path) -> None:
        """Returns ScssWatcher when watch_stylesheet=True for SCSS file."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("QWidget { color: red; }")

        config = EntryConfig(stylesheet=str(scss_file), watch_stylesheet=True)
        watcher = _apply_stylesheet(qapp, config)

        assert_that(watcher).is_not_none()
        assert_that(type(watcher).__name__).is_equal_to("ScssWatcher")
        watcher.stop()  # type: ignore[union-attr]

    def test_ignores_watch_for_qrc_paths(self, qapp: App) -> None:
        """watch_stylesheet is ignored for QRC paths."""
        mock_file = MagicMock()
        mock_file.open.return_value = True

        mock_stream = MagicMock()
        mock_stream.readAll.return_value = "QWidget { color: blue; }"

        with (
            patch("qtpie.entrypoint.QFile", return_value=mock_file),
            patch("qtpie.entrypoint.QTextStream", return_value=mock_stream),
        ):
            config = EntryConfig(stylesheet=":/styles/app.qss", watch_stylesheet=True)
            result = _apply_stylesheet(qapp, config)

        # Should load once and not return a watcher (can't watch QRC)
        assert_that(result).is_none()
        assert_that(qapp.styleSheet()).contains("color: blue")


class TestEntrypointStylesheetConfig:
    """Tests for @entrypoint decorator with stylesheet config."""

    def test_entrypoint_stores_stylesheet_config(self) -> None:
        """@entrypoint should store stylesheet config on decorated function."""

        @entrypoint(stylesheet="styles.qss", watch_stylesheet=True)
        def my_main() -> QLabel:
            return QLabel("Hi")

        assert_that(hasattr(my_main, ENTRY_CONFIG_ATTR)).is_true()
        config = getattr(my_main, ENTRY_CONFIG_ATTR)
        assert_that(config.stylesheet).is_equal_to("styles.qss")
        assert_that(config.watch_stylesheet).is_true()

    def test_entrypoint_stores_scss_search_paths(self) -> None:
        """@entrypoint should store scss_search_paths config."""

        @entrypoint(
            stylesheet="styles.scss",
            scss_search_paths=["path/to/partials", "path/to/themes"],
        )
        def my_main() -> QLabel:
            return QLabel("Hi")

        config = getattr(my_main, ENTRY_CONFIG_ATTR)
        assert_that(config.stylesheet).is_equal_to("styles.scss")
        assert_that(config.scss_search_paths).is_equal_to(("path/to/partials", "path/to/themes"))

    def test_widget_with_stylesheet_still_usable(self, qapp: App) -> None:
        """Widget with @entrypoint and stylesheet config is still usable."""

        @entrypoint(stylesheet="nonexistent.qss")
        @widget
        class TestWidget(Widget):
            label: QLabel = new("Hello!")

        # Should still work (stylesheet doesn't exist but that's fine)
        w = TestWidget()
        assert_that(w.label.text()).is_equal_to("Hello!")
