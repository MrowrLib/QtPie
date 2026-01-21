# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
"""Tests for State callback bubbling through parent hierarchy."""

from typing import Any

from assertpy import assert_that

from qtpie import State, Variable, new, state
from qtpie.event import Event


class TestCallbackBubblingBasics:
    """Basic callback bubbling functionality."""

    def test_callback_found_on_self(self) -> None:
        """onChange calls method on same State."""
        calls: list[int] = []

        @state
        class MyState(State):
            count: Variable[int] = new(0, onChange="_on_count")

            def _on_count(self, value: int) -> None:
                calls.append(value)

        s = MyState()
        s.count.value = 42

        assert_that(calls).is_equal_to([42])

    def test_callback_bubbles_to_parent(self) -> None:
        """onChange bubbles up when not found on self."""
        calls: list[str] = []

        # Define child first so parent can reference it
        @state
        class ChildState(State):
            name: Variable[str] = new("", onChange="on_child_changed")
            # No on_child_changed method here - it bubbles up!

        @state
        class ParentState(State):
            children: Variable[list[Any]] = new([])  # Use Any to avoid forward ref

            def on_child_changed(self) -> None:
                calls.append("parent_notified")

        parent = ParentState()
        child = ChildState()
        parent.children.append(child)  # Auto-parents

        child.name.value = "new_name"

        assert_that(calls).is_equal_to(["parent_notified"])

    def test_callback_bubbles_multiple_levels(self) -> None:
        """Grandparent receives bubbled callback."""
        calls: list[str] = []

        # Define from leaf to root
        @state
        class ChildState(State):
            value: Variable[int] = new(0, onChange="on_deep_change")
            # No on_deep_change here

        @state
        class ParentState(State):
            children: Variable[list[Any]] = new([])
            # No on_deep_change here

        @state
        class GrandparentState(State):
            children: Variable[list[Any]] = new([])

            def on_deep_change(self) -> None:
                calls.append("grandparent_notified")

        grandparent = GrandparentState()
        parent = ParentState()
        child = ChildState()

        grandparent.children.append(parent)
        parent.children.append(child)

        child.value.value = 123

        assert_that(calls).is_equal_to(["grandparent_notified"])


class TestCallbackWithEvent:
    """Callback bubbling with Event emission."""

    def test_callback_emits_parent_event(self) -> None:
        """onChange finds parent's Event and emits it."""
        calls: list[str] = []

        @state
        class ChildState(State):
            data: Variable[str] = new("", onChange="on_save")

        @state
        class ParentState(State):
            on_save: Event = Event()
            children: Variable[list[Any]] = new([])

        parent = ParentState()
        parent.on_save.connect(lambda: calls.append("event_fired"))

        child = ChildState()
        parent.children.append(child)

        child.data.value = "new_data"

        assert_that(calls).is_equal_to(["event_fired"])

    def test_bubbled_event_triggers_handler_via_setup(self) -> None:
        """Full chain: child change -> parent event -> handler (manual wiring in __setup__)."""
        calls: list[str] = []

        @state
        class ChildState(State):
            value: Variable[int] = new(0, onChange="on_save")

        @state
        class ParentState(State):
            on_save: Event = Event()
            children: Variable[list[Any]] = new([])

            def __setup__(self) -> None:
                self.on_save.connect(self._on_save)

            def _on_save(self) -> None:
                calls.append("saved")

        parent = ParentState()
        child = ChildState()
        parent.children.append(child)

        child.value.value = 42

        assert_that(calls).is_equal_to(["saved"])

    def test_event_wired_via_decorator(self) -> None:
        """@state(on_save="_handler") wires Event to handler automatically."""
        calls: list[str] = []

        @state(on_save="_persist")
        class MyState(State):
            on_save: Event  # Annotation-only, auto-created
            data: Variable[str] = new("")

            def _persist(self) -> None:
                calls.append("persisted")

        s = MyState()
        s.on_save.emit()  # Manual emit should trigger _persist

        assert_that(calls).is_equal_to(["persisted"])

    def test_event_annotation_creates_event_instance(self) -> None:
        """Event annotation without assignment creates Event instance."""

        @state
        class MyState(State):
            on_something: Event  # No = Event() needed

        s = MyState()

        # Should have an Event instance
        assert_that(s.on_something).is_instance_of(Event)

        # Should be functional
        received: list[str] = []
        s.on_something.connect(lambda: received.append("called"))
        s.on_something.emit()

        assert_that(received).is_equal_to(["called"])

    def test_full_chain_with_decorator_wiring(self) -> None:
        """Full chain: child change -> parent event (annotation) -> handler (decorator-wired)."""
        calls: list[str] = []

        @state
        class ChildState(State):
            value: Variable[int] = new(0, onChange="on_save")

        @state(on_save="_persist")
        class ParentState(State):
            on_save: Event  # Annotation-only!
            children: Variable[list[Any]] = new([])

            def _persist(self) -> None:
                calls.append("persisted")

        parent = ParentState()
        child = ChildState()
        parent.children.append(child)

        # Child change should bubble to parent's Event and trigger _persist
        child.value.value = 42

        assert_that(calls).is_equal_to(["persisted"])


class TestCallbackWithListChanges:
    """Callback bubbling with list operations."""

    def test_list_append_bubbles_callback(self) -> None:
        """onInsert callback can bubble to parent."""
        calls: list[str] = []

        @state
        class ChildState(State):
            items: Variable[list[str]] = new([], onInsert="on_item_added")

        @state
        class ParentState(State):
            children: Variable[list[Any]] = new([])

            def on_item_added(self, item: str) -> None:
                calls.append(f"added:{item}")

        parent = ParentState()
        child = ChildState()
        parent.children.append(child)

        child.items.append("hello")

        assert_that(calls).is_equal_to(["added:hello"])
