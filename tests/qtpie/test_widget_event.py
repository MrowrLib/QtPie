# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for Event annotation in Widget creating real Qt Signal."""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Event, Widget, new, widget
from qtpie.testing import QtDriver


class TestWidgetEventAnnotation:
    """Event annotation in Widget creates real Qt Signal."""

    def test_event_annotation_creates_signal(self, qt: QtDriver) -> None:
        """Event annotation without assignment creates real Qt Signal."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello")
            on_click: Event  # Should become Signal()

        w = qt.track(MyWidget())

        # Should have a Signal (can connect and emit)
        received: list[bool] = []
        w.on_click.connect(lambda: received.append(True))
        w.on_click.emit()

        assert_that(received).is_equal_to([True])

    def test_event_annotation_with_type_arg(self, qt: QtDriver) -> None:
        """Event[int] annotation creates Signal(int)."""

        @widget
        class MyWidget(Widget):
            on_value_changed: Event[int]

        w = qt.track(MyWidget())

        received: list[int] = []
        w.on_value_changed.connect(lambda x: received.append(x))
        w.on_value_changed.emit(42)

        assert_that(received).is_equal_to([42])

    def test_event_annotation_with_tuple_args(self, qt: QtDriver) -> None:
        """Event[tuple[int, str]] annotation creates Signal(int, str)."""

        @widget
        class MyWidget(Widget):
            on_update: Event[tuple[int, str]]

        w = qt.track(MyWidget())

        received: list[tuple[int, str]] = []
        w.on_update.connect(lambda x, y: received.append((x, y)))
        w.on_update.emit(42, "hello")

        assert_that(received).is_equal_to([(42, "hello")])

    def test_event_wired_via_decorator(self, qt: QtDriver) -> None:
        """@widget(on_something="_handler") wires Signal to handler."""
        calls: list[str] = []

        @widget(on_save="_on_save")
        class MyWidget(Widget):
            on_save: Event

            def _on_save(self) -> None:
                calls.append("saved")

        w = qt.track(MyWidget())
        w.on_save.emit()

        assert_that(calls).is_equal_to(["saved"])

    def test_multiple_event_annotations(self, qt: QtDriver) -> None:
        """Multiple Event annotations all become Signals."""

        @widget
        class MyWidget(Widget):
            on_first: Event
            on_second: Event[int]
            on_third: Event[str]

        w = qt.track(MyWidget())

        first_calls: list[bool] = []
        second_calls: list[int] = []
        third_calls: list[str] = []

        w.on_first.connect(lambda: first_calls.append(True))
        w.on_second.connect(lambda x: second_calls.append(x))
        w.on_third.connect(lambda x: third_calls.append(x))

        w.on_first.emit()
        w.on_second.emit(123)
        w.on_third.emit("hello")

        assert_that(first_calls).is_equal_to([True])
        assert_that(second_calls).is_equal_to([123])
        assert_that(third_calls).is_equal_to(["hello"])

    def test_explicit_signal_not_overwritten(self, qt: QtDriver) -> None:
        """Explicit Signal assignment is not overwritten by Event processing."""
        from qtpy.QtCore import Signal

        @widget
        class MyWidget(Widget):
            # Explicit Signal should be preserved
            on_explicit: Event = Signal(str)  # type: ignore[assignment]

        w = qt.track(MyWidget())

        received: list[str] = []
        w.on_explicit.connect(lambda x: received.append(x))
        w.on_explicit.emit("test")

        assert_that(received).is_equal_to(["test"])
