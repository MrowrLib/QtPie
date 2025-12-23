"""Tests for the @stylesheet decorator."""

from __future__ import annotations

from pathlib import Path

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie import App, widget
from qtpie.decorators.stylesheet import (
    STYLESHEET_CONFIG_ATTR,
    STYLESHEET_WATCHER_ATTR,
    stylesheet,
)
from qtpie.styles.watcher import QssWatcher, ScssWatcher
from qtpie_test import QtDriver


class TestStylesheetDecoratorConfig:
    """Tests for @stylesheet config storage."""

    def test_stores_config_on_class(self) -> None:
        """@stylesheet should store config on decorated class."""

        @stylesheet("styles.qss")
        class TestWidget(QWidget):
            pass

        assert_that(hasattr(TestWidget, STYLESHEET_CONFIG_ATTR)).is_true()
        config = getattr(TestWidget, STYLESHEET_CONFIG_ATTR)
        assert_that(config["path"]).is_equal_to("styles.qss")
        assert_that(config["watch"]).is_false()
        assert_that(config["scss_search_paths"]).is_none()

    def test_stores_config_with_all_options(self) -> None:
        """@stylesheet should store all config options."""

        @stylesheet("main.scss", watch=True, scss_search_paths=["partials/"])
        class TestWidget(QWidget):
            pass

        config = getattr(TestWidget, STYLESHEET_CONFIG_ATTR)
        assert_that(config["path"]).is_equal_to("main.scss")
        assert_that(config["watch"]).is_true()
        assert_that(config["scss_search_paths"]).is_equal_to(["partials/"])


class TestStylesheetDecoratorLoading:
    """Tests for @stylesheet loading functionality."""

    def test_loads_qss_file(self, qt: QtDriver, tmp_path: Path) -> None:
        """@stylesheet should load QSS from filesystem."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        @stylesheet(str(qss_file))
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(w.styleSheet()).contains("background-color: red")

    def test_compiles_scss_file(self, qt: QtDriver, tmp_path: Path) -> None:
        """@stylesheet should compile and apply SCSS."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("$color: blue; QWidget { background-color: $color; }")

        @stylesheet(str(scss_file))
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(w.styleSheet()).contains("background-color: blue")

    def test_scss_auto_adds_parent_folder(self, qt: QtDriver, tmp_path: Path) -> None:
        """SCSS compilation should auto-add parent folder as search path."""
        partial = tmp_path / "_variables.scss"
        partial.write_text("$bg: green;")

        scss_file = tmp_path / "main.scss"
        scss_file.write_text("@import 'variables'; QWidget { background: $bg; }")

        @stylesheet(str(scss_file))
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(w.styleSheet()).contains("background: green")

    def test_scss_explicit_search_paths(self, qt: QtDriver, tmp_path: Path) -> None:
        """SCSS with explicit search paths should use only those paths."""
        partials_dir = tmp_path / "partials"
        partials_dir.mkdir()
        partial = partials_dir / "_colors.scss"
        partial.write_text("$primary: purple;")

        scss_file = tmp_path / "main.scss"
        scss_file.write_text("@import 'colors'; QWidget { color: $primary; }")

        @stylesheet(str(scss_file), scss_search_paths=[str(partials_dir)])
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(w.styleSheet()).contains("color: purple")

    def test_handles_missing_file_gracefully(self, qt: QtDriver) -> None:
        """@stylesheet should handle missing files without crashing."""

        @stylesheet("/nonexistent/path/styles.qss")
        class TestWidget(QWidget):
            pass

        # Should not raise
        w = TestWidget()
        qt.track(w)
        # Stylesheet will be empty but no crash
        assert_that(w.styleSheet()).is_equal_to("")


class TestStylesheetDecoratorWatching:
    """Tests for @stylesheet watching functionality."""

    def test_creates_qss_watcher_when_watching(self, qt: QtDriver, tmp_path: Path) -> None:
        """@stylesheet should create QssWatcher when watch=True."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: white; }")

        @stylesheet(str(qss_file), watch=True)
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(hasattr(w, STYLESHEET_WATCHER_ATTR)).is_true()
        watcher = getattr(w, STYLESHEET_WATCHER_ATTR)
        assert_that(watcher).is_instance_of(QssWatcher)
        watcher.stop()

    def test_creates_scss_watcher_when_watching_scss(self, qt: QtDriver, tmp_path: Path) -> None:
        """@stylesheet should create ScssWatcher when watching SCSS."""
        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("QWidget { color: cyan; }")

        @stylesheet(str(scss_file), watch=True)
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(hasattr(w, STYLESHEET_WATCHER_ATTR)).is_true()
        watcher = getattr(w, STYLESHEET_WATCHER_ATTR)
        assert_that(watcher).is_instance_of(ScssWatcher)
        watcher.stop()

    def test_no_watcher_without_watch_flag(self, qt: QtDriver, tmp_path: Path) -> None:
        """@stylesheet should not create watcher when watch=False."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: black; }")

        @stylesheet(str(qss_file), watch=False)
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(hasattr(w, STYLESHEET_WATCHER_ATTR)).is_false()


class TestStylesheetWithWidgetDecorator:
    """Tests for @stylesheet combined with @widget."""

    def test_works_with_widget_decorator(self, qt: QtDriver, tmp_path: Path) -> None:
        """@stylesheet should work when combined with @widget."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: orange; }")

        @stylesheet(str(qss_file))
        @widget
        class TestWidget(QWidget):
            pass

        w = TestWidget()
        qt.track(w)

        assert_that(w.styleSheet()).contains("background-color: orange")


class TestStylesheetOnApplication:
    """Tests for @stylesheet on QApplication subclasses."""

    def test_applies_to_app(self, qapp: App, tmp_path: Path) -> None:
        """@stylesheet should work on QApplication subclasses."""
        # Note: We can't actually instantiate a new QApplication in tests
        # since one already exists. We just test that the decorator stores config.
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: red; }")

        @stylesheet(str(qss_file))
        class MyApp(App):
            pass

        # Verify config is stored
        assert_that(hasattr(MyApp, STYLESHEET_CONFIG_ATTR)).is_true()
        config = getattr(MyApp, STYLESHEET_CONFIG_ATTR)
        assert_that(config["path"]).is_equal_to(str(qss_file))
