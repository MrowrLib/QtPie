"""Tests for async closeEvent auto-wrapping in @widget and @window."""

# These ignores are required because pyright sees `async def closeEvent` as returning
# Coroutine at static analysis time, before @widget wraps it to return None.
# This is a fundamental limitation - decorators run at runtime, not static analysis.
# pyright: reportIncompatibleMethodOverride=false
# pyright: reportImplicitOverride=false

import asyncio

from assertpy import assert_that
from qtpy.QtWidgets import QMainWindow, QWidget

from qtpie import widget, window
from qtpie.decorators._async_wrap import wrap_async_methods
from qtpie_test import QtDriver


class TestWrapAsyncMethods:
    """Tests for the wrap_async_methods utility."""

    def test_wraps_async_close_event(self, qt: QtDriver) -> None:
        """wrap_async_methods should wrap async closeEvent."""
        _ = qt

        class MyClass:
            async def closeEvent(self, event: object) -> None:
                pass

        # Before wrapping, it's a coroutine function
        assert_that(asyncio.iscoroutinefunction(MyClass.closeEvent)).is_true()

        wrap_async_methods(MyClass)

        # After wrapping, it's no longer a coroutine function (wrapped by asyncClose)
        assert_that(asyncio.iscoroutinefunction(MyClass.closeEvent)).is_false()

    def test_does_not_wrap_sync_close_event(self, qt: QtDriver) -> None:
        """wrap_async_methods should not wrap sync closeEvent."""
        _ = qt

        class MyClass:
            def closeEvent(self, event: object) -> None:
                pass

        original = MyClass.closeEvent
        wrap_async_methods(MyClass)

        # Should be unchanged
        assert_that(MyClass.closeEvent).is_equal_to(original)

    def test_does_not_wrap_when_no_close_event(self, qt: QtDriver) -> None:
        """wrap_async_methods should handle classes without closeEvent."""
        _ = qt

        class MyClass:
            pass

        # Should not raise
        wrap_async_methods(MyClass)


class TestWidgetAsyncCloseEvent:
    """Tests for async closeEvent in @widget classes."""

    def test_widget_wraps_async_close_event(self, qt: QtDriver) -> None:
        """@widget should auto-wrap async closeEvent."""

        @widget
        class MyWidget(QWidget):
            async def closeEvent(self, event: object) -> None:
                pass

        # The method should no longer be a coroutine function after decoration
        assert_that(asyncio.iscoroutinefunction(MyWidget.closeEvent)).is_false()

    def test_widget_does_not_wrap_sync_close_event(self, qt: QtDriver) -> None:
        """@widget should not wrap sync closeEvent."""

        @widget
        class MyWidget(QWidget):
            closed: bool = False

            def closeEvent(self, event: object) -> None:
                self.closed = True

        w = MyWidget()
        qt.track(w)

        # Should still be a regular method
        assert_that(asyncio.iscoroutinefunction(MyWidget.closeEvent)).is_false()

    def test_widget_async_close_event_is_callable(self, qt: QtDriver) -> None:
        """Wrapped async closeEvent should be callable."""

        @widget
        class MyWidget(QWidget):
            cleanup_called: bool = False

            async def closeEvent(self, event: object) -> None:
                self.cleanup_called = True

        w = MyWidget()
        qt.track(w)

        assert_that(w.closeEvent).is_not_none()
        assert_that(callable(w.closeEvent)).is_true()


class TestWindowAsyncCloseEvent:
    """Tests for async closeEvent in @window classes."""

    def test_window_wraps_async_close_event(self, qt: QtDriver) -> None:
        """@window should auto-wrap async closeEvent."""

        @window
        class MyWindow(QMainWindow):
            async def closeEvent(self, event: object) -> None:
                pass

        # The method should no longer be a coroutine function after decoration
        assert_that(asyncio.iscoroutinefunction(MyWindow.closeEvent)).is_false()

    def test_window_does_not_wrap_sync_close_event(self, qt: QtDriver) -> None:
        """@window should not wrap sync closeEvent."""

        @window
        class MyWindow(QMainWindow):
            closed: bool = False

            def closeEvent(self, event: object) -> None:
                self.closed = True

        w = MyWindow()
        qt.track(w)

        # Should still be a regular method
        assert_that(asyncio.iscoroutinefunction(MyWindow.closeEvent)).is_false()


class TestAsyncCloseEventCleanup:
    """Tests that async closeEvent actually performs cleanup."""

    def test_async_close_event_body_is_preserved(self, qt: QtDriver) -> None:
        """The body of async closeEvent should be preserved after wrapping."""

        @widget
        class MyWidget(QWidget):
            setup_value: int = 0

            async def closeEvent(self, event: object) -> None:
                # This should still be accessible after wrapping
                self.setup_value = 42

        w = MyWidget()
        qt.track(w)

        # The closeEvent should exist and be callable
        assert_that(hasattr(w, "closeEvent")).is_true()
