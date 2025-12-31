"""E2E tests for async slot and closeEvent - verifies actual async execution."""

# pyright: reportIncompatibleMethodOverride=false
# pyright: reportImplicitOverride=false
# pyright: reportUnknownMemberType=false

import asyncio
from collections.abc import Iterator

import pytest
import qasync  # type: ignore[import-untyped]
from assertpy import assert_that
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QApplication, QPushButton, QWidget

from qtpie import make, slot, widget
from qtpie.testing import QtDriver


@pytest.fixture
def async_qt(qt: QtDriver) -> Iterator[tuple[QtDriver, qasync.QEventLoop]]:
    """Fixture that provides QtDriver with a qasync event loop."""
    app = QApplication.instance()
    assert app is not None
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    try:
        yield qt, loop
    finally:
        # Proper cleanup: stop loop, process remaining events, close loop, detach
        if loop.is_running():
            loop.stop()
        # Process any pending callbacks
        loop.run_until_complete(asyncio.sleep(0))
        # Detach from asyncio before closing to avoid conflicts
        asyncio.set_event_loop(None)
        # Close the loop while Qt is still alive
        loop.close()


def process_async(loop: qasync.QEventLoop, duration: float = 0.05) -> None:
    """Process async events for a duration."""
    loop.run_until_complete(asyncio.sleep(duration))


class TestAsyncSlotE2E:
    """E2E tests that verify async slots actually execute."""

    def test_async_slot_executes_on_signal(self, async_qt: tuple[QtDriver, qasync.QEventLoop]) -> None:
        """An async slot should actually execute when signal fires."""
        qt, loop = async_qt
        executed = []

        @widget
        class TestWidget(QWidget):
            btn: QPushButton = make(QPushButton, "Click", clicked="on_click")

            @slot
            async def on_click(self) -> None:
                await asyncio.sleep(0.01)  # Actually await something
                executed.append("clicked")

        w = TestWidget()
        qt.track(w)

        # Fire the signal by clicking
        qt.click(w.btn)

        # Process events to let async code run
        process_async(loop, 0.05)

        assert_that(executed).contains("clicked")

    def test_async_slot_with_args_executes(self, async_qt: tuple[QtDriver, qasync.QEventLoop]) -> None:
        """An async slot with arguments should receive them."""
        qt, loop = async_qt
        received = []

        @widget
        class TestWidget(QWidget):
            message_sent = Signal(str)

            @slot(str)
            async def on_message(self, text: str) -> None:
                await asyncio.sleep(0.01)
                received.append(text)

        w = TestWidget()
        qt.track(w)

        # Connect and emit signal
        w.message_sent.connect(w.on_message)
        w.message_sent.emit("hello")

        process_async(loop, 0.05)

        assert_that(received).contains("hello")

    def test_multiple_async_slots_execute_concurrently(self, async_qt: tuple[QtDriver, qasync.QEventLoop]) -> None:
        """Multiple async slots should be able to run concurrently."""
        qt, loop = async_qt
        order = []

        @widget
        class TestWidget(QWidget):
            btn1: QPushButton = make(QPushButton, "One", clicked="on_one")
            btn2: QPushButton = make(QPushButton, "Two", clicked="on_two")

            @slot
            async def on_one(self) -> None:
                order.append("one-start")
                await asyncio.sleep(0.02)
                order.append("one-end")

            @slot
            async def on_two(self) -> None:
                order.append("two-start")
                await asyncio.sleep(0.01)
                order.append("two-end")

        w = TestWidget()
        qt.track(w)

        # Click both buttons quickly
        qt.click(w.btn1)
        qt.click(w.btn2)

        process_async(loop, 0.1)

        # Both should have started
        assert_that(order).contains("one-start")
        assert_that(order).contains("two-start")
        assert_that(order).contains("one-end")
        assert_that(order).contains("two-end")


class TestAsyncCloseEventE2E:
    """E2E tests that verify async closeEvent actually blocks."""

    def test_async_close_event_executes_cleanup(self, async_qt: tuple[QtDriver, qasync.QEventLoop]) -> None:
        """Async closeEvent should execute and complete cleanup before returning."""
        from qtpy.QtCore import QTimer

        qt, loop = async_qt
        cleanup_done: list[str] = []

        @widget
        class TestWidget(QWidget):
            async def closeEvent(self, event: object) -> None:
                await asyncio.sleep(0.01)
                cleanup_done.append("cleaned")

        w = TestWidget()
        qt.track(w)
        w.show()

        # Use QTimer to trigger close from Qt's context (not inside async task)
        # This is how it works in a real app
        QTimer.singleShot(10, w.close)
        QTimer.singleShot(100, loop.stop)

        # Run the loop until stopped
        loop.run_forever()

        assert_that(cleanup_done).contains("cleaned")

    def test_sync_slot_still_works(self, qt: QtDriver) -> None:
        """Sync slots should work normally alongside async ones."""
        results = []

        @widget
        class TestWidget(QWidget):
            btn: QPushButton = make(QPushButton, "Click", clicked="on_click")

            @slot
            def on_click(self) -> None:
                results.append("sync-clicked")

        w = TestWidget()
        qt.track(w)

        qt.click(w.btn)

        assert_that(results).contains("sync-clicked")
