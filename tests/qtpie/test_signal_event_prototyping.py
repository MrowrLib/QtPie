# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Prototype: Can Event[int] annotation create a real Qt Signal?"""

from assertpy import assert_that
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget

from qtpie.testing import QtDriver


class TestSignalBasics:
    """First, understand how Qt Signals actually work."""

    def test_signal_is_class_attribute(self, qt: QtDriver) -> None:
        """Signal must be defined as class attribute."""

        class MyWidget(QWidget):
            my_signal = Signal(int)

        w = MyWidget()
        qt.track(w)

        received: list[int] = []
        w.my_signal.connect(lambda x: received.append(x))
        w.my_signal.emit(42)
        assert_that(received).is_equal_to([42])

    def test_signal_created_dynamically_after_class(self, qt: QtDriver) -> None:
        """Can we add a Signal to a class after definition? (Probably not)"""

        class MyWidget(QWidget):
            pass

        # Try to add signal after class is defined
        MyWidget.late_signal = Signal(int)  # type: ignore[attr-defined]

        w = MyWidget()
        qt.track(w)

        # Does it work?
        received: list[int] = []
        try:
            w.late_signal.connect(lambda x: received.append(x))  # type: ignore[attr-defined]
            w.late_signal.emit(42)  # type: ignore[attr-defined]
            assert_that(received).is_equal_to([42])
            print("LATE SIGNAL WORKS!")
        except Exception as e:
            print(f"Late signal failed (expected): {e}")
            # This is expected to fail - just documenting Qt's behavior

    def test_signal_created_in_init_subclass(self, qt: QtDriver) -> None:
        """Can __init_subclass__ create signals?"""

        class SignalBase(QWidget):
            def __init_subclass__(cls, **kwargs: object) -> None:
                super().__init_subclass__(**kwargs)
                # Try to create signal from annotation
                for name, hint in getattr(cls, "__annotations__", {}).items():
                    if _is_event_hint(hint):
                        # Don't override if already set
                        if name not in cls.__dict__:
                            setattr(cls, name, Signal(int))

        class MyWidget(SignalBase):
            on_click: Event[int]  # Just an annotation

        w = MyWidget()
        qt.track(w)

        received: list[int] = []
        try:
            w.on_click.connect(lambda x: received.append(x))  # type: ignore[attr-defined]
            w.on_click.emit(42)  # type: ignore[attr-defined]
            assert_that(received).is_equal_to([42])
            print("__init_subclass__ SIGNAL WORKS!")
        except Exception as e:
            print(f"__init_subclass__ signal failed: {e}")
            raise


class TestEventAnnotation:
    """Test Event[T] annotation approach."""

    def test_event_annotation_creates_signal_via_init_subclass(self, qt: QtDriver) -> None:
        """Event[int] annotation should create a real Signal via __init_subclass__."""

        class EventBase(QWidget):
            def __init_subclass__(cls, **kwargs: object) -> None:
                super().__init_subclass__(**kwargs)
                _process_event_annotations(cls)

        class MyWidget(EventBase):
            on_something: Event[int]

        w = MyWidget()
        qt.track(w)

        received: list[int] = []
        w.on_something.connect(lambda x: received.append(x))  # type: ignore[attr-defined]
        w.on_something.emit(42)  # type: ignore[attr-defined]
        assert_that(received).is_equal_to([42])

    def test_event_annotation_no_args(self, qt: QtDriver) -> None:
        """Event (no type param) should create a Signal with no args."""

        class EventBase(QWidget):
            def __init_subclass__(cls, **kwargs: object) -> None:
                super().__init_subclass__(**kwargs)
                _process_event_annotations(cls)

        class MyWidget(EventBase):
            on_click: Event  # No type param = no args

        w = MyWidget()
        qt.track(w)

        received: list[str] = []
        w.on_click.connect(lambda: received.append("clicked"))  # type: ignore[attr-defined]
        w.on_click.emit()  # type: ignore[attr-defined]
        assert_that(received).is_equal_to(["clicked"])


# --- Helper functions for prototyping ---


def _is_event_hint(hint: object) -> bool:
    """Check if a type hint is Event[T] or Event."""
    if isinstance(hint, str):
        return hint.startswith("Event[") or hint == "Event"

    origin = getattr(hint, "__origin__", None)
    if origin is not None:
        return getattr(origin, "__name__", "") == "Event"

    return getattr(hint, "__name__", "") == "Event"


def _extract_signal_args(hint: object) -> tuple[type, ...]:
    """Extract types from Event[T] to pass to Signal().

    Returns tuple of types, e.g.:
    - Event -> ()
    - Event[int] -> (int,)
    - Event[tuple[int, str]] -> (int, str)  # Unpacked
    """
    import typing

    if isinstance(hint, str):
        if hint == "Event":
            return ()
        # Parse Event[int] from string - simplified
        if hint.startswith("Event[") and hint.endswith("]"):
            type_str = hint[6:-1]
            # Very simplified type parsing
            if type_str == "int":
                return (int,)
            elif type_str == "str":
                return (str,)
            elif type_str == "bool":
                return (bool,)
            elif type_str == "float":
                return (float,)
        return ()

    # Handle actual Event type with generic args
    origin = typing.get_origin(hint)
    if origin is not None:
        args = typing.get_args(hint)
        if args:
            arg = args[0]
            # Unpack tuple types
            if typing.get_origin(arg) is tuple:
                return typing.get_args(arg)
            return (arg,)
    return ()


def _process_event_annotations(cls: type) -> None:
    """Process Event[T] annotations and create real Signals."""
    import typing

    # Use get_type_hints to resolve forward references and get actual types
    try:
        hints = typing.get_type_hints(cls)
    except Exception:
        hints = {}
    annotations = hints or getattr(cls, "__annotations__", {})
    for name, hint in annotations.items():
        if _is_event_hint(hint):
            if name not in cls.__dict__:
                args = _extract_signal_args(hint)
                setattr(cls, name, Signal(*args))


# Placeholder Event class for type hints
class Event[T = None]:
    """Marker type for event annotations. Creates real Qt Signal in Widget context."""

    pass
