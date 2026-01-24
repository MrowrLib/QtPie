"""Tests for zoom/scale functionality."""

# pyright: reportPrivateUsage=false

from pathlib import Path

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie.styles import clear_scss_variables, compile_scss, get_scss_variables, get_zoom, set_scss_variable, set_zoom
from qtpie.styles.zoom import get_base_font_size, set_base_font_size
from qtpie.testing import QtDriver


class TestScssVariableInjection:
    """Tests for SCSS variable injection in compiler."""

    def setup_method(self) -> None:
        """Clear variables before each test."""
        clear_scss_variables()

    def teardown_method(self) -> None:
        """Clear variables after each test."""
        clear_scss_variables()

    def test_compile_without_variables(self, tmp_path: Path) -> None:
        """Compiles normally when no variables are set."""
        scss_file = tmp_path / "test.scss"
        scss_file.write_text("QWidget { color: red; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(str(scss_file), str(qss_file))

        assert_that(qss_file.exists()).is_true()
        qss = qss_file.read_text()
        assert_that(qss).contains("color: red")

    def test_compile_with_local_variables(self, tmp_path: Path) -> None:
        """Compiles with locally passed variables."""
        scss_file = tmp_path / "test.scss"
        scss_file.write_text("QWidget { color: $my-color; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(
            str(scss_file),
            str(qss_file),
            variables={"my-color": "blue"},
        )

        qss = qss_file.read_text()
        assert_that(qss).contains("color: blue")

    def test_compile_with_global_variables(self, tmp_path: Path) -> None:
        """Compiles with globally set variables."""
        set_scss_variable("accent", "#ff0000")

        scss_file = tmp_path / "test.scss"
        scss_file.write_text("QWidget { background: $accent; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(str(scss_file), str(qss_file))

        qss = qss_file.read_text()
        assert_that(qss).contains("background: #ff0000")

    def test_local_variables_override_global(self, tmp_path: Path) -> None:
        """Local variables take precedence over global."""
        set_scss_variable("color", "red")

        scss_file = tmp_path / "test.scss"
        scss_file.write_text("QWidget { color: $color; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(
            str(scss_file),
            str(qss_file),
            variables={"color": "green"},
        )

        qss = qss_file.read_text()
        assert_that(qss).contains("color: green")

    def test_scss_can_override_injected_defaults(self, tmp_path: Path) -> None:
        """SCSS file can override injected !default variables."""
        set_scss_variable("scale", "1.0")

        scss_file = tmp_path / "test.scss"
        # SCSS defines its own value, should take precedence
        scss_file.write_text("$scale: 2.0;\nQWidget { zoom: $scale; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(str(scss_file), str(qss_file))

        qss = qss_file.read_text()
        assert_that(qss).contains("zoom: 2")

    def test_disable_global_variables(self, tmp_path: Path) -> None:
        """Can disable global variable injection."""
        set_scss_variable("color", "red")

        scss_file = tmp_path / "test.scss"
        scss_file.write_text("$color: blue;\nQWidget { color: $color; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(str(scss_file), str(qss_file), use_global_variables=False)

        qss = qss_file.read_text()
        # Without global injection, SCSS's own $color: blue is used
        assert_that(qss).contains("color: blue")

    def test_scale_variable_for_math(self, tmp_path: Path) -> None:
        """Scale variable can be used in SCSS math expressions."""
        set_scss_variable("scale", "2")

        scss_file = tmp_path / "test.scss"
        scss_file.write_text("QWidget { padding: 4px * $scale; }")
        qss_file = tmp_path / "output.qss"

        compile_scss(str(scss_file), str(qss_file))

        qss = qss_file.read_text()
        assert_that(qss).contains("padding: 8px")


class TestZoomFunctions:
    """Tests for zoom getter/setter functions."""

    def setup_method(self) -> None:
        """Reset zoom state before each test."""
        clear_scss_variables()
        # Reset zoom to default without triggering recompile (no callback set)
        from qtpie.styles import zoom

        zoom._zoom_scale = 1.0
        zoom._base_font_size_pt = 10.0

    def teardown_method(self) -> None:
        """Clean up after each test."""
        clear_scss_variables()
        from qtpie.styles import zoom

        zoom._zoom_scale = 1.0
        zoom._base_font_size_pt = 10.0

    def test_get_zoom_default(self) -> None:
        """Default zoom is 1.0."""
        assert_that(get_zoom()).is_equal_to(1.0)

    def test_set_zoom_updates_scale(self, qt: QtDriver) -> None:
        """set_zoom updates the zoom scale."""
        set_zoom(1.5)
        assert_that(get_zoom()).is_equal_to(1.5)

    def test_set_zoom_sets_scss_variable(self, qt: QtDriver) -> None:
        """set_zoom sets the $scale SCSS variable."""
        set_zoom(2.0)
        variables = get_scss_variables()
        assert_that(variables).contains_key("scale")
        assert_that(variables["scale"]).is_equal_to("2.0")

    def test_get_base_font_size_default(self) -> None:
        """Default base font size is 10pt."""
        assert_that(get_base_font_size()).is_equal_to(10.0)

    def test_set_base_font_size(self, qt: QtDriver) -> None:
        """set_base_font_size updates the base size."""
        set_base_font_size(12.0)
        assert_that(get_base_font_size()).is_equal_to(12.0)


class TestZoomWithWatcher:
    """Tests for zoom integration with ScssWatcher."""

    def setup_method(self) -> None:
        """Reset zoom state."""
        clear_scss_variables()
        from qtpie.styles import zoom

        zoom._zoom_scale = 1.0
        zoom._recompile_callback = None

    def teardown_method(self) -> None:
        """Clean up."""
        clear_scss_variables()
        from qtpie.styles import zoom

        zoom._zoom_scale = 1.0
        zoom._recompile_callback = None

    def test_watcher_uses_global_scale(self, qt: QtDriver, tmp_path: Path) -> None:
        """ScssWatcher uses global $scale variable."""
        from qtpie.styles import watch_scss

        widget = QWidget()
        qt.track(widget)

        set_scss_variable("scale", "1.5")

        scss_file = tmp_path / "test.scss"
        scss_file.write_text("QWidget { padding: 10px * $scale; }")
        qss_file = tmp_path / "output.qss"

        watcher = watch_scss(widget, str(scss_file), str(qss_file))

        assert_that(widget.styleSheet()).contains("padding: 15px")
        watcher.stop()

    def test_set_zoom_triggers_recompile(self, qt: QtDriver, tmp_path: Path) -> None:
        """set_zoom triggers stylesheet recompilation."""
        from qtpie.styles import watch_scss

        widget = QWidget()
        qt.track(widget)

        scss_file = tmp_path / "test.scss"
        scss_file.write_text("$scale: 1 !default;\nQWidget { padding: 10px * $scale; }")
        qss_file = tmp_path / "output.qss"

        watcher = watch_scss(widget, str(scss_file), str(qss_file))

        # Initial compile with default scale
        assert_that(widget.styleSheet()).contains("padding: 10px")

        # Change zoom
        set_zoom(2.0)

        # Should recompile with new scale
        assert_that(widget.styleSheet()).contains("padding: 20px")
        watcher.stop()
