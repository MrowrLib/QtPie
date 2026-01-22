# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownLambdaType=false
"""Tests for State hierarchy methods: var() and emit_event().

These methods enable States to resolve Variables and Events by walking
up the state_parent chain, similar to how Widgets walk up the Qt parent chain.
"""

import pytest
from assertpy import assert_that

from qtpie import Event, State, Variable, new, state

# =============================================================================
# Test State Classes
# =============================================================================


@state
class RootState(State):
    """Root state with some Variables and Events."""

    config_value: Variable[str] = new("root_config")
    shared_count: Variable[int] = new(100)
    on_root_event: Event
    on_data_changed: Event[str]


@state
class MiddleState(State):
    """Middle-level state with its own Variables."""

    middle_value: Variable[str] = new("middle")
    on_middle_event: Event


@state
class LeafState(State):
    """Leaf state that will access parent Variables/Events."""

    leaf_value: Variable[str] = new("leaf")
    on_leaf_event: Event


# =============================================================================
# var() Tests
# =============================================================================


class TestStateVar:
    """Test State.var() method for Variable resolution from hierarchy."""

    def test_var_resolves_from_self(self) -> None:
        """var() finds Variable on self."""

        @state
        class MyState(State):
            count: Variable[int] = new(42)

        s = MyState()
        result = s.var("count")
        assert_that(result).is_equal_to(42)

    def test_var_resolves_with_underscore_prefix(self) -> None:
        """var() finds Variable with underscore prefix."""

        @state
        class MyState(State):
            _private_value: Variable[str] = new("secret")

        s = MyState()
        # Can access with or without underscore
        assert_that(s.var("_private_value")).is_equal_to("secret")
        assert_that(s.var("private_value")).is_equal_to("secret")

    def test_var_resolves_from_parent(self) -> None:
        """var() finds Variable from state_parent."""
        root = RootState()
        leaf = LeafState()
        leaf.state_parent = root

        # Leaf should find root's config_value
        result = leaf.var("config_value")
        assert_that(result).is_equal_to("root_config")

    def test_var_resolves_from_grandparent(self) -> None:
        """var() walks up multiple levels to find Variable."""
        root = RootState()
        middle = MiddleState()
        leaf = LeafState()

        middle.state_parent = root
        leaf.state_parent = middle

        # Leaf should find root's config_value (two levels up)
        result = leaf.var("config_value")
        assert_that(result).is_equal_to("root_config")

    def test_var_prefers_closer_parent(self) -> None:
        """var() returns Variable from nearest parent in hierarchy."""

        @state
        class ParentState(State):
            theme: Variable[str] = new("parent_theme")

        @state
        class ChildState(State):
            theme: Variable[str] = new("child_theme")

        parent = ParentState()
        child = ChildState()
        child.state_parent = parent

        # Child should find its own theme, not parent's
        assert_that(child.var("theme")).is_equal_to("child_theme")

    def test_var_raises_if_not_found(self) -> None:
        """var() raises AttributeError if Variable not in hierarchy."""

        @state
        class EmptyState(State):
            pass

        s = EmptyState()
        with pytest.raises(AttributeError, match="not found"):
            s.var("nonexistent")

    def test_var_returns_unwrapped_value(self) -> None:
        """var() returns the unwrapped value, not the Variable object."""

        @state
        class MyState(State):
            items: Variable[list[str]] = new(["a", "b", "c"])

        s = MyState()
        result = s.var("items")

        # Should be the list value, not Variable
        assert_that(result).is_instance_of(list)
        assert_that(result).is_equal_to(["a", "b", "c"])

    def test_var_with_non_variable_attribute(self) -> None:
        """var() returns non-Variable attributes directly."""

        @state
        class MyState(State):
            regular_attr: str = "plain_string"

        s = MyState()
        result = s.var("regular_attr")
        assert_that(result).is_equal_to("plain_string")

    def test_var_type_hints(self) -> None:
        """var() type overloads work correctly (compile-time check)."""

        @state
        class MyState(State):
            count: Variable[int] = new(42)
            name: Variable[str] = new("test")

        s = MyState()

        # These should type-check correctly
        x: int = s.var("count", int)
        y: str = s.var("name", str)
        z: int | str = s.var("count", int, str)
        w: int | None = s.var("count", int, None)

        assert_that(x).is_equal_to(42)
        assert_that(y).is_equal_to("test")
        assert_that(z).is_equal_to(42)
        assert_that(w).is_equal_to(42)


# =============================================================================
# emit_event() Tests
# =============================================================================


class TestStateEmitEvent:
    """Test State.emit_event() method for Event resolution and emission."""

    def test_emit_event_on_self(self) -> None:
        """emit_event() finds and emits Event on self."""
        received: list[str] = []

        @state
        class MyState(State):
            on_action: Event

        s = MyState()
        s.on_action.connect(lambda: received.append("fired"))

        s.emit_event("on_action")
        assert_that(received).is_equal_to(["fired"])

    def test_emit_event_with_args(self) -> None:
        """emit_event() passes arguments to Event.emit()."""
        received: list[tuple[str, int]] = []

        @state
        class MyState(State):
            on_data: Event[str]

        s = MyState()
        s.on_data.connect(lambda msg: received.append(("data", len(msg))))

        s.emit_event("on_data", "hello")
        assert_that(received).is_equal_to([("data", 5)])

    def test_emit_event_from_parent(self) -> None:
        """emit_event() finds Event in state_parent."""
        received: list[str] = []

        root = RootState()
        root.on_root_event.connect(lambda: received.append("root_fired"))

        leaf = LeafState()
        leaf.state_parent = root

        # Leaf emits root's event
        leaf.emit_event("on_root_event")
        assert_that(received).is_equal_to(["root_fired"])

    def test_emit_event_from_grandparent(self) -> None:
        """emit_event() walks up multiple levels."""
        received: list[str] = []

        root = RootState()
        root.on_root_event.connect(lambda: received.append("root_fired"))

        middle = MiddleState()
        middle.state_parent = root

        leaf = LeafState()
        leaf.state_parent = middle

        # Leaf emits root's event (two levels up)
        leaf.emit_event("on_root_event")
        assert_that(received).is_equal_to(["root_fired"])

    def test_emit_event_prefers_closer_parent(self) -> None:
        """emit_event() emits Event from nearest parent."""
        root_received: list[str] = []
        middle_received: list[str] = []

        @state
        class ParentState(State):
            on_notify: Event

        @state
        class ChildState(State):
            on_notify: Event

        parent = ParentState()
        parent.on_notify.connect(lambda: root_received.append("parent"))

        child = ChildState()
        child.on_notify.connect(lambda: middle_received.append("child"))
        child.state_parent = parent

        # Child should emit its own event
        child.emit_event("on_notify")

        assert_that(root_received).is_empty()
        assert_that(middle_received).is_equal_to(["child"])

    def test_emit_event_raises_if_not_found(self) -> None:
        """emit_event() raises AttributeError if Event not in hierarchy."""

        @state
        class EmptyState(State):
            pass

        s = EmptyState()
        with pytest.raises(AttributeError, match="not found"):
            s.emit_event("nonexistent_event")

    def test_emit_event_with_underscore_prefix(self) -> None:
        """emit_event() finds Event with underscore prefix."""
        received: list[str] = []

        @state
        class MyState(State):
            _on_private: Event

        s = MyState()
        s._on_private.connect(lambda: received.append("private"))

        # Can emit with or without underscore
        s.emit_event("_on_private")
        s.emit_event("on_private")

        assert_that(received).is_equal_to(["private", "private"])

    def test_emit_event_typed_event_with_args(self) -> None:
        """emit_event() works with Event[T] and typed arguments."""
        received: list[str] = []

        root = RootState()
        root.on_data_changed.connect(lambda msg: received.append(msg))

        leaf = LeafState()
        leaf.state_parent = root

        leaf.emit_event("on_data_changed", "new_data")
        assert_that(received).is_equal_to(["new_data"])


# =============================================================================
# event() Tests
# =============================================================================


class TestStateEvent:
    """Test State.event() method for Event resolution."""

    def test_event_resolves_from_self(self) -> None:
        """event() finds Event on self."""

        @state
        class MyState(State):
            on_action: Event

        s = MyState()
        evt = s.event("on_action")
        assert_that(evt).is_instance_of(Event)

    def test_event_resolves_from_parent(self) -> None:
        """event() finds Event from state_parent."""
        root = RootState()
        leaf = LeafState()
        leaf.state_parent = root

        evt = leaf.event("on_root_event")
        assert_that(evt).is_same_as(root.on_root_event)

    def test_event_raises_if_not_found(self) -> None:
        """event() raises AttributeError if Event not in hierarchy."""

        @state
        class EmptyState(State):
            pass

        s = EmptyState()
        with pytest.raises(AttributeError, match="not found"):
            s.event("nonexistent")


# =============================================================================
# Combined Hierarchy Tests
# =============================================================================


class TestStateHierarchyCombined:
    """Test combined usage of var() and emit_event() in realistic scenarios."""

    def test_child_reads_parent_config_and_emits_event(self) -> None:
        """Child state reads parent config and emits parent event."""
        events: list[str] = []

        @state
        class AppState(State):
            app_name: Variable[str] = new("MyApp")
            on_action_completed: Event[str]

        @state
        class ChildFeature(State):
            def do_work(self) -> None:
                # Read parent's config
                app = self.var("app_name", str)
                # Emit parent's event
                self.emit_event("on_action_completed", f"Work done for {app}")

        app = AppState()
        app.on_action_completed.connect(lambda msg: events.append(msg))

        child = ChildFeature()
        child.state_parent = app

        child.do_work()

        assert_that(events).is_equal_to(["Work done for MyApp"])

    def test_deep_hierarchy_variable_and_event_resolution(self) -> None:
        """Variables and Events resolve correctly in deep hierarchies."""
        events: list[str] = []

        @state
        class Level0(State):
            level0_value: Variable[str] = new("L0")
            on_l0_event: Event

        @state
        class Level1(State):
            level1_value: Variable[str] = new("L1")

        @state
        class Level2(State):
            level2_value: Variable[str] = new("L2")

        @state
        class Level3(State):
            def check_hierarchy(self) -> list[str]:
                return [
                    self.var("level2_value", str),
                    self.var("level1_value", str),
                    self.var("level0_value", str),
                ]

            def trigger_root_event(self) -> None:
                self.emit_event("on_l0_event")

        l0 = Level0()
        l0.on_l0_event.connect(lambda: events.append("L0_event"))

        l1 = Level1()
        l1.state_parent = l0

        l2 = Level2()
        l2.state_parent = l1

        l3 = Level3()
        l3.state_parent = l2

        # Check variable resolution
        values = l3.check_hierarchy()
        assert_that(values).is_equal_to(["L2", "L1", "L0"])

        # Check event emission
        l3.trigger_root_event()
        assert_that(events).is_equal_to(["L0_event"])
