"""Tests for the @entrypoint decorator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from assertpy import assert_that
from qtpy.QtWidgets import QApplication, QLabel, QWidget

from qtpie import entrypoint, make, widget
from qtpie.decorators.entrypoint import (
    ENTRY_CONFIG_ATTR,
    EntryConfig,
    _apply_stylesheet,  # pyright: ignore[reportPrivateUsage]
    _compile_scss_to_string,  # pyright: ignore[reportPrivateUsage]
    _is_main_module,  # pyright: ignore[reportPrivateUsage]
    _should_auto_run,  # pyright: ignore[reportPrivateUsage]
)
from qtpie.styles.watcher import QssWatcher, ScssWatcher

if TYPE_CHECKING:
    from qtpie import App


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
        class TestWidget(QWidget):
            label: QLabel = make(QLabel, "Test")

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
        class TestWidget(QWidget):
            label: QLabel = make(QLabel, "Test")

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
        class TestWidget(QWidget):
            label: QLabel = make(QLabel, "Hello!")

        # Should be able to instantiate and use the widget
        w = TestWidget()
        assert_that(w.label.text()).is_equal_to("Hello!")


class TestEntryPointStylesheetConfig:
    """Tests for @entrypoint stylesheet configuration."""

    def test_entry_config_stylesheet_defaults(self) -> None:
        """EntryConfig should have default stylesheet settings."""
        config = EntryConfig()
        assert_that(config.stylesheet).is_none()
        assert_that(config.watch_stylesheet).is_false()
        assert_that(config.scss_search_paths).is_equal_to(())

    def test_entry_config_stylesheet_custom_values(self) -> None:
        """EntryConfig should accept custom stylesheet values."""
        config = EntryConfig(
            stylesheet="styles.scss",
            watch_stylesheet=True,
            scss_search_paths=("folder1", "folder2"),
        )
        assert_that(config.stylesheet).is_equal_to("styles.scss")
        assert_that(config.watch_stylesheet).is_true()
        assert_that(config.scss_search_paths).is_equal_to(("folder1", "folder2"))

    def test_entrypoint_stores_stylesheet_config(self) -> None:
        """@entrypoint should store stylesheet config on decorated function."""

        @entrypoint(
            stylesheet="app.qss",
            watch_stylesheet=True,
            scss_search_paths=["partials/"],
        )
        def my_main() -> QLabel:
            return QLabel("Hi")

        config = getattr(my_main, ENTRY_CONFIG_ATTR)
        assert_that(config.stylesheet).is_equal_to("app.qss")
        assert_that(config.watch_stylesheet).is_true()
        assert_that(config.scss_search_paths).is_equal_to(("partials/",))


class TestEntryPointStylesheetLoading:
    """Tests for @entrypoint stylesheet loading functionality."""

    def test_apply_stylesheet_loads_qss_file(self, qapp: App, tmp_path: Path) -> None:
        """_apply_stylesheet should load QSS from filesystem."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        config = EntryConfig(stylesheet=str(qss_file))
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        _apply_stylesheet(app, config)

        assert_that(app.styleSheet()).contains("background-color: red")

    def test_apply_stylesheet_compiles_scss_file(self, qapp: App, tmp_path: Path) -> None:
        """_apply_stylesheet should compile and apply SCSS."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("$color: blue; QWidget { background-color: $color; }")

        config = EntryConfig(stylesheet=str(scss_file))
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        _apply_stylesheet(app, config)

        assert_that(app.styleSheet()).contains("background-color: blue")

    def test_apply_stylesheet_scss_auto_adds_parent_folder(self, qapp: App, tmp_path: Path) -> None:
        """SCSS compilation should auto-add parent folder as search path."""
        # Create a partial in the same folder
        partial = tmp_path / "_variables.scss"
        partial.write_text("$bg: green;")

        scss_file = tmp_path / "main.scss"
        scss_file.write_text("@import 'variables'; QWidget { background: $bg; }")

        config = EntryConfig(stylesheet=str(scss_file))
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        _apply_stylesheet(app, config)

        assert_that(app.styleSheet()).contains("background: green")

    def test_apply_stylesheet_scss_explicit_search_paths(self, qapp: App, tmp_path: Path) -> None:
        """SCSS with explicit search paths should use only those paths."""
        # Create partials in a subdirectory
        partials_dir = tmp_path / "partials"
        partials_dir.mkdir()
        partial = partials_dir / "_colors.scss"
        partial.write_text("$primary: purple;")

        scss_file = tmp_path / "main.scss"
        scss_file.write_text("@import 'colors'; QWidget { color: $primary; }")

        config = EntryConfig(
            stylesheet=str(scss_file),
            scss_search_paths=(str(partials_dir),),
        )
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        _apply_stylesheet(app, config)

        assert_that(app.styleSheet()).contains("color: purple")

    def test_apply_stylesheet_returns_qss_watcher_when_watching(self, qapp: App, tmp_path: Path) -> None:
        """_apply_stylesheet should return QssWatcher when watch_stylesheet=True."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: white; }")

        config = EntryConfig(stylesheet=str(qss_file), watch_stylesheet=True)
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        watcher = _apply_stylesheet(app, config)

        assert_that(watcher).is_instance_of(QssWatcher)
        assert watcher is not None
        watcher.stop()

    def test_apply_stylesheet_returns_scss_watcher_when_watching_scss(self, qapp: App, tmp_path: Path) -> None:
        """_apply_stylesheet should return ScssWatcher when watching SCSS."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("QWidget { color: cyan; }")

        config = EntryConfig(stylesheet=str(scss_file), watch_stylesheet=True)
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        watcher = _apply_stylesheet(app, config)

        assert_that(watcher).is_instance_of(ScssWatcher)
        assert watcher is not None
        watcher.stop()

    def test_apply_stylesheet_no_watcher_without_watch_flag(self, qapp: App, tmp_path: Path) -> None:
        """_apply_stylesheet should return None when watch_stylesheet=False."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: black; }")

        config = EntryConfig(stylesheet=str(qss_file), watch_stylesheet=False)
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        watcher = _apply_stylesheet(app, config)

        assert_that(watcher).is_none()

    def test_apply_stylesheet_handles_missing_file_gracefully(self, qapp: App) -> None:
        """_apply_stylesheet should handle missing files without crashing."""
        config = EntryConfig(stylesheet="/nonexistent/path/styles.qss")
        app = QApplication.instance()
        assert isinstance(app, QApplication)

        # Should not raise
        watcher = _apply_stylesheet(app, config)
        assert_that(watcher).is_none()

    def test_compile_scss_to_string(self, tmp_path: Path) -> None:
        """_compile_scss_to_string should compile SCSS to a string."""
        scss_file = tmp_path / "test.scss"
        scss_file.write_text("$size: 10px; QWidget { padding: $size; }")

        result = _compile_scss_to_string(str(scss_file), [str(tmp_path)])

        assert_that(result).contains("padding: 10px")
