# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for Event - pure Python event emitter."""

from assertpy import assert_that

from qtpie.event import Event, extract_event_args, is_event_hint


class TestEventBasics:
    """Basic Event functionality."""

    def test_event_emit_no_args(self) -> None:
        """Event with no args can emit and call handler."""
        event: Event = Event()
        called: list[bool] = []

        event.connect(lambda: called.append(True))
        event.emit()

        assert_that(called).is_equal_to([True])

    def test_event_emit_with_args(self) -> None:
        """Event can emit with arguments."""
        event: Event[int] = Event()
        received: list[int] = []

        event.connect(lambda x: received.append(x))
        event.emit(42)

        assert_that(received).is_equal_to([42])

    def test_event_multiple_handlers(self) -> None:
        """Multiple handlers are all called."""
        event: Event[str] = Event()
        calls: list[str] = []

        event.connect(lambda s: calls.append(f"handler1:{s}"))
        event.connect(lambda s: calls.append(f"handler2:{s}"))
        event.emit("hello")

        assert_that(calls).contains("handler1:hello", "handler2:hello")

    def test_event_disconnect(self) -> None:
        """Disconnected handler is not called."""
        event: Event = Event()
        calls: list[str] = []

        def handler() -> None:
            calls.append("called")

        event.connect(handler)
        event.emit()
        assert_that(calls).is_equal_to(["called"])

        event.disconnect(handler)
        event.emit()
        # Should still be just one call
        assert_that(calls).is_equal_to(["called"])

    def test_event_multiple_args(self) -> None:
        """Event can emit multiple arguments."""
        event: Event[tuple[int, str]] = Event()
        received: list[tuple[int, str]] = []

        event.connect(lambda x, y: received.append((x, y)))
        event.emit(42, "hello")

        assert_that(received).is_equal_to([(42, "hello")])


class TestIsEventHint:
    """Tests for is_event_hint helper."""

    def test_plain_event_string(self) -> None:
        """'Event' string is recognized."""
        assert_that(is_event_hint("Event")).is_true()

    def test_generic_event_string(self) -> None:
        """'Event[int]' string is recognized."""
        assert_that(is_event_hint("Event[int]")).is_true()
        assert_that(is_event_hint("Event[str]")).is_true()
        assert_that(is_event_hint("Event[tuple[int, str]]")).is_true()

    def test_plain_event_type(self) -> None:
        """Event type is recognized."""
        assert_that(is_event_hint(Event)).is_true()

    def test_generic_event_type(self) -> None:
        """Event[int] type is recognized."""
        assert_that(is_event_hint(Event[int])).is_true()
        assert_that(is_event_hint(Event[str])).is_true()

    def test_non_event_not_recognized(self) -> None:
        """Non-Event types are not recognized."""
        assert_that(is_event_hint("str")).is_false()
        assert_that(is_event_hint("int")).is_false()
        assert_that(is_event_hint(int)).is_false()
        assert_that(is_event_hint(str)).is_false()
        assert_that(is_event_hint("Variable[int]")).is_false()


class TestExtractEventArgs:
    """Tests for extract_event_args helper."""

    def test_plain_event_string(self) -> None:
        """'Event' returns empty tuple."""
        assert_that(extract_event_args("Event")).is_equal_to(())

    def test_single_arg_string(self) -> None:
        """'Event[int]' returns (int,)."""
        assert_that(extract_event_args("Event[int]")).is_equal_to((int,))
        assert_that(extract_event_args("Event[str]")).is_equal_to((str,))

    def test_tuple_arg_string(self) -> None:
        """'Event[tuple[int, str]]' returns (int, str)."""
        assert_that(extract_event_args("Event[tuple[int, str]]")).is_equal_to((int, str))

    def test_plain_event_type(self) -> None:
        """Event type returns empty tuple."""
        assert_that(extract_event_args(Event)).is_equal_to(())

    def test_single_arg_type(self) -> None:
        """Event[int] type returns (int,)."""
        assert_that(extract_event_args(Event[int])).is_equal_to((int,))

    def test_tuple_arg_type(self) -> None:
        """Event[tuple[int, str]] type returns (int, str)."""
        assert_that(extract_event_args(Event[tuple[int, str]])).is_equal_to((int, str))
