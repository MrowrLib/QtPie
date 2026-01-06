"""Tests for the @entrypoint decorator."""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QWidget

from qtpie import App, Widget, entrypoint, new, widget
from qtpie.entrypoint import (
    ENTRY_CONFIG_ATTR,
    EntryConfig,
    _is_main_module,  # pyright: ignore[reportPrivateUsage]
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
