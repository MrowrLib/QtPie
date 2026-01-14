# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for size= parameter on @widget, @window, and @app decorators."""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import AppBase, app, new
from qtpie.testing import QtDriver

from .conftest import QWIDGET_CLASS_TYPES, create_and_track


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestDecoratorSize:
    """@decorator(size=...) parameter sets initial widget size."""

    def test_size_sets_initial_dimensions(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(size=(width, height)) sets initial size via resize()."""

        @decorator(size=(800, 600))
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.width()).is_equal_to(800)
        assert_that(instance.height()).is_equal_to(600)

    def test_size_not_set_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Without size=, widget uses default Qt sizing."""

        @decorator
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        # Just verify we can access size - don't assert specific values
        # as default sizing varies by widget type and platform
        assert_that(instance.width()).is_greater_than_or_equal_to(0)
        assert_that(instance.height()).is_greater_than_or_equal_to(0)

    def test_size_with_large_dimensions(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(size=...) works with large dimensions."""

        @decorator(size=(1920, 1080))
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.width()).is_equal_to(1920)
        assert_that(instance.height()).is_equal_to(1080)

    def test_size_with_small_dimensions(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(size=...) works with small dimensions."""

        @decorator(size=(100, 50))
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.width()).is_equal_to(100)
        assert_that(instance.height()).is_equal_to(50)


class TestAppSize:
    """@app(size=...) sets size on the auto-created window."""

    def test_app_size_sets_window_dimensions(self, qt: QtDriver) -> None:
        """@app(size=(width, height)) sets size on the window."""

        @app(size=(1024, 768))
        class TestApp(AppBase):
            # Need a widget field to trigger window creation
            _label: QLabel = new("Hello")

        instance = TestApp()
        assert instance.window is not None
        qt.track(instance.window)

        assert_that(instance.window.width()).is_equal_to(1024)
        assert_that(instance.window.height()).is_equal_to(768)
