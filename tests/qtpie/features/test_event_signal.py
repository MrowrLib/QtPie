# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownMemberType=false
"""Tests for Event[T] annotation creating real Qt Signals across all class types.

Event annotations on QtPie classes (Widget, Window, Dialog, Menu, App, WidgetBase)
should automatically create real Qt Signals.

Note: State creates pure Python Events, not Qt Signals (different behavior).
"""

import pytest
from assertpy import assert_that

from qtpie import Event, Variable, new
from qtpie.testing import QtDriver

from .conftest import SIGNAL_CLASS_TYPES, create_and_track


@pytest.mark.parametrize("base_class,decorator", SIGNAL_CLASS_TYPES)
class TestEventAnnotationCreatesSignal:
    """Event annotation creates real Qt Signal across all class types."""

    def test_bare_event_annotation_creates_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Event annotation becomes a Qt Signal."""

        @decorator
        class TestClass(base_class):
            on_test: Event

        instance = create_and_track(qt, TestClass, base_class)

        # Should have a Signal (can connect and emit)
        received: list[bool] = []
        instance.on_test.connect(lambda: received.append(True))
        instance.on_test.emit()

        assert_that(received).is_equal_to([True])

    def test_event_with_int_type_creates_typed_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """Event[int] annotation becomes Signal(int)."""

        @decorator
        class TestClass(base_class):
            on_value: Event[int]

        instance = create_and_track(qt, TestClass, base_class)

        received: list[int] = []
        instance.on_value.connect(lambda x: received.append(x))
        instance.on_value.emit(42)

        assert_that(received).is_equal_to([42])

    def test_event_with_str_type_creates_typed_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """Event[str] annotation becomes Signal(str)."""

        @decorator
        class TestClass(base_class):
            on_name: Event[str]

        instance = create_and_track(qt, TestClass, base_class)

        received: list[str] = []
        instance.on_name.connect(lambda x: received.append(x))
        instance.on_name.emit("hello")

        assert_that(received).is_equal_to(["hello"])

    def test_event_with_tuple_args_creates_multi_arg_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """Event[tuple[int, str]] annotation becomes Signal(int, str)."""

        @decorator
        class TestClass(base_class):
            on_update: Event[tuple[int, str]]

        instance = create_and_track(qt, TestClass, base_class)

        received: list[tuple[int, str]] = []
        instance.on_update.connect(lambda x, y: received.append((x, y)))
        instance.on_update.emit(42, "hello")

        assert_that(received).is_equal_to([(42, "hello")])

    def test_multiple_event_annotations(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple Event annotations all become Signals."""

        @decorator
        class TestClass(base_class):
            on_first: Event
            on_second: Event[int]
            on_third: Event[str]

        instance = create_and_track(qt, TestClass, base_class)

        first_calls: list[bool] = []
        second_calls: list[int] = []
        third_calls: list[str] = []

        instance.on_first.connect(lambda: first_calls.append(True))
        instance.on_second.connect(lambda x: second_calls.append(x))
        instance.on_third.connect(lambda x: third_calls.append(x))

        instance.on_first.emit()
        instance.on_second.emit(123)
        instance.on_third.emit("world")

        assert_that(first_calls).is_equal_to([True])
        assert_that(second_calls).is_equal_to([123])
        assert_that(third_calls).is_equal_to(["world"])

    def test_event_signal_can_be_wired_via_decorator(self, base_class, decorator, qt: QtDriver) -> None:
        """Event Signal can be wired to handler via decorator."""
        calls: list[str] = []

        @decorator(on_save="_on_save")
        class TestClass(base_class):
            on_save: Event

            def _on_save(self) -> None:
                calls.append("saved")

        instance = create_and_track(qt, TestClass, base_class)
        instance.on_save.emit()

        assert_that(calls).is_equal_to(["saved"])

    def test_explicit_signal_not_overwritten(self, base_class, decorator, qt: QtDriver) -> None:
        """Explicit Signal assignment is not overwritten by Event processing."""
        from qtpy.QtCore import Signal

        @decorator
        class TestClass(base_class):
            # Explicit Signal should be preserved
            on_explicit: Event = Signal(str)  # type: ignore[assignment]

        instance = create_and_track(qt, TestClass, base_class)

        received: list[str] = []
        instance.on_explicit.connect(lambda x: received.append(x))
        instance.on_explicit.emit("test")

        assert_that(received).is_equal_to(["test"])

    def test_event_with_variable_coexist(self, base_class, decorator, qt: QtDriver) -> None:
        """Event and Variable can coexist on same class."""
        calls: list[int] = []

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            on_count_changed: Event[int]

            def increment(self) -> None:
                self._count.value += 1
                self.on_count_changed.emit(self._count.value)

        instance = create_and_track(qt, TestClass, base_class)
        instance.on_count_changed.connect(lambda x: calls.append(x))

        instance.increment()
        instance.increment()

        assert_that(calls).is_equal_to([1, 2])
        assert_that(instance._count.value).is_equal_to(2)

    def test_emit_event_emits_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """emit_event() emits the underlying Qt Signal."""
        calls: list[bool] = []

        @decorator
        class TestClass(base_class):
            on_action: Event

            def trigger(self) -> None:
                self.emit_event("on_action")

        instance = create_and_track(qt, TestClass, base_class)
        instance.on_action.connect(lambda: calls.append(True))

        instance.trigger()

        assert_that(calls).is_equal_to([True])

    def test_emit_event_with_args(self, base_class, decorator, qt: QtDriver) -> None:
        """emit_event() passes arguments to Signal."""
        calls: list[tuple[int, str]] = []

        @decorator
        class TestClass(base_class):
            on_data: Event[tuple[int, str]]

            def send_data(self, num: int, text: str) -> None:
                self.emit_event("on_data", num, text)

        instance = create_and_track(qt, TestClass, base_class)
        instance.on_data.connect(lambda x, y: calls.append((x, y)))

        instance.send_data(42, "hello")

        assert_that(calls).is_equal_to([(42, "hello")])
