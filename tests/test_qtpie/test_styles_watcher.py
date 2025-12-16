"""Tests for stylesheet watchers."""

import time
from pathlib import Path

from assertpy import assert_that
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QWidget

from qtpie.styles import watch_qss, watch_scss, watch_styles
from qtpie_test import QtDriver

FIXTURES = Path(__file__).parent / "fixtures" / "scss"


class TestQssWatcher:
    """Tests for QssWatcher."""

    def test_applies_existing_file_on_start(self, qt: QtDriver, tmp_path: Path) -> None:
        """Applies stylesheet from existing file immediately."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        watcher = watch_qss(widget, str(qss_file))

        assert_that(widget.styleSheet()).contains("background-color: red")
        watcher.stop()

    def test_reloads_on_file_change(self, qt: QtDriver, tmp_path: Path) -> None:
        """Reloads stylesheet when file changes."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        watcher = watch_qss(widget, str(qss_file))
        assert_that(widget.styleSheet()).contains("red")

        # Change the file
        qss_file.write_text("QWidget { background-color: blue; }")

        # Wait for debounce + file system events
        QTest.qWait(200)

        assert_that(widget.styleSheet()).contains("blue")
        watcher.stop()

    def test_watches_nonexistent_file_and_applies_when_created(self, qt: QtDriver, tmp_path: Path) -> None:
        """Watches for file creation and applies when file appears."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "styles.qss"
        # File doesn't exist yet

        watcher = watch_qss(widget, str(qss_file))

        # No stylesheet yet
        assert_that(widget.styleSheet()).is_equal_to("")

        # Create the file
        qss_file.write_text("QWidget { background-color: green; }")

        # Wait for directory watcher to pick it up
        QTest.qWait(200)

        assert_that(widget.styleSheet()).contains("green")
        watcher.stop()

    def test_handles_editor_delete_recreate(self, qt: QtDriver, tmp_path: Path) -> None:
        """Handles editor save behavior that deletes and recreates file."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        watcher = watch_qss(widget, str(qss_file))
        assert_that(widget.styleSheet()).contains("red")

        # Simulate editor delete + recreate (like vim does)
        qss_file.unlink()
        time.sleep(0.05)  # Small delay between delete and create
        qss_file.write_text("QWidget { background-color: yellow; }")

        QTest.qWait(200)

        assert_that(widget.styleSheet()).contains("yellow")
        watcher.stop()

    def test_works_with_qwidget_target(self, qt: QtDriver, tmp_path: Path) -> None:
        """Works when target is a QWidget."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: white; }")

        watcher = watch_qss(widget, str(qss_file))

        assert_that(widget.styleSheet()).contains("color: white")
        watcher.stop()


class TestScssWatcher:
    """Tests for ScssWatcher."""

    def test_compiles_and_applies_on_start(self, qt: QtDriver, tmp_path: Path) -> None:
        """Compiles SCSS and applies on start."""
        widget = QWidget()
        qt.track(widget)

        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("$color: purple; QWidget { background-color: $color; }")
        qss_file = tmp_path / "output.qss"

        watcher = watch_scss(widget, str(scss_file), str(qss_file))

        assert_that(qss_file.exists()).is_true()
        assert_that(widget.styleSheet()).contains("purple")
        watcher.stop()

    def test_recompiles_on_scss_change(self, qt: QtDriver, tmp_path: Path) -> None:
        """Recompiles when SCSS file changes."""
        widget = QWidget()
        qt.track(widget)

        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("QWidget { background-color: red; }")
        qss_file = tmp_path / "output.qss"

        watcher = watch_scss(widget, str(scss_file), str(qss_file))
        assert_that(widget.styleSheet()).contains("red")

        # Change SCSS
        scss_file.write_text("QWidget { background-color: cyan; }")
        QTest.qWait(200)

        assert_that(widget.styleSheet()).contains("cyan")
        watcher.stop()

    def test_recompiles_on_imported_file_change(self, qt: QtDriver, tmp_path: Path) -> None:
        """Recompiles when an imported SCSS file changes."""
        widget = QWidget()
        qt.track(widget)

        # Create partials directory
        partials = tmp_path / "partials"
        partials.mkdir()

        variables = partials / "_variables.scss"
        variables.write_text("$bg: orange;")

        scss_file = tmp_path / "main.scss"
        scss_file.write_text("@import 'variables'; QWidget { background: $bg; }")
        qss_file = tmp_path / "output.qss"

        watcher = watch_scss(widget, str(scss_file), str(qss_file), search_paths=[str(partials)])
        assert_that(widget.styleSheet()).contains("orange")

        # Change the imported file
        variables.write_text("$bg: pink;")
        QTest.qWait(200)

        assert_that(widget.styleSheet()).contains("pink")
        watcher.stop()

    def test_uses_fixture_with_two_search_dirs(self, qt: QtDriver, tmp_path: Path) -> None:
        """Works with multiple search directories."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "output.qss"

        watcher = watch_scss(
            widget,
            str(FIXTURES / "two_search_dirs" / "main.scss"),
            str(qss_file),
            search_paths=[
                str(FIXTURES / "two_search_dirs" / "core"),
                str(FIXTURES / "two_search_dirs" / "themes"),
            ],
        )

        assert_that(widget.styleSheet()).contains("#ff6600")  # $accent-color
        watcher.stop()


class TestWatchStyles:
    """Tests for watch_styles convenience function."""

    def test_returns_scss_watcher_when_scss_path_provided(self, qt: QtDriver, tmp_path: Path) -> None:
        """Returns ScssWatcher when scss_path is provided."""
        widget = QWidget()
        qt.track(widget)

        scss_file = tmp_path / "styles.scss"
        scss_file.write_text("QWidget { color: red; }")
        qss_file = tmp_path / "output.qss"

        watcher = watch_styles(widget, str(qss_file), scss_path=str(scss_file))

        assert_that(type(watcher).__name__).is_equal_to("ScssWatcher")
        watcher.stop()

    def test_returns_qss_watcher_when_no_scss_path(self, qt: QtDriver, tmp_path: Path) -> None:
        """Returns QssWatcher when scss_path is None."""
        widget = QWidget()
        qt.track(widget)

        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QWidget { color: blue; }")

        watcher = watch_styles(widget, str(qss_file))

        assert_that(type(watcher).__name__).is_equal_to("QssWatcher")
        watcher.stop()
