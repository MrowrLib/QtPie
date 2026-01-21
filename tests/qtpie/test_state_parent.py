# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
"""Tests for State parent hierarchy."""

from assertpy import assert_that

from qtpie import State, Variable, new, state


class TestStateParentBasics:
    """Basic state_parent functionality."""

    def test_state_parent_initially_none(self) -> None:
        """New state has no parent."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)

        s = MyState()
        assert_that(s.state_parent).is_none()

    def test_state_parent_set_manually(self) -> None:
        """Can set parent explicitly."""

        @state
        class ParentState(State):
            name: Variable[str] = new("parent")

        @state
        class ChildState(State):
            value: Variable[int] = new(0)

        parent = ParentState()
        child = ChildState()

        child.state_parent = parent

        assert_that(child.state_parent).is_same_as(parent)

    def test_state_parent_can_be_cleared(self) -> None:
        """Parent can be set back to None."""

        @state
        class ParentState(State):
            pass

        @state
        class ChildState(State):
            pass

        parent = ParentState()
        child = ChildState()

        child.state_parent = parent
        assert_that(child.state_parent).is_same_as(parent)

        child.state_parent = None
        assert_that(child.state_parent).is_none()

    def test_state_parent_chain(self) -> None:
        """Can have grandparent chain."""

        @state
        class GrandparentState(State):
            pass

        @state
        class ParentState(State):
            pass

        @state
        class ChildState(State):
            pass

        grandparent = GrandparentState()
        parent = ParentState()
        child = ChildState()

        parent.state_parent = grandparent
        child.state_parent = parent

        assert_that(child.state_parent).is_same_as(parent)
        assert_that(child.state_parent.state_parent).is_same_as(grandparent)  # pyright: ignore[reportOptionalMemberAccess]
        assert_that(child.state_parent.state_parent.state_parent).is_none()  # pyright: ignore[reportOptionalMemberAccess]


class TestAutoParenting:
    """Auto-parenting when State children are added to Variable[list[State]]."""

    def test_auto_parent_on_list_append(self) -> None:
        """Appending State to Variable[list[State]] auto-parents."""

        @state
        class ChildState(State):
            value: Variable[int] = new(0)

        @state
        class ParentState(State):
            children: Variable[list[ChildState]] = new([])

        parent = ParentState()
        child = ChildState()

        assert_that(child.state_parent).is_none()

        parent.children.append(child)

        assert_that(child.state_parent).is_same_as(parent)

    def test_auto_parent_on_list_insert(self) -> None:
        """Inserting State to list auto-parents."""

        @state
        class ChildState(State):
            pass

        @state
        class ParentState(State):
            children: Variable[list[ChildState]] = new([])

        parent = ParentState()
        child = ChildState()

        parent.children.insert(0, child)

        assert_that(child.state_parent).is_same_as(parent)

    def test_auto_parent_multiple_children(self) -> None:
        """Multiple children all get parented."""

        @state
        class ChildState(State):
            pass

        @state
        class ParentState(State):
            children: Variable[list[ChildState]] = new([])

        parent = ParentState()
        child1 = ChildState()
        child2 = ChildState()
        child3 = ChildState()

        parent.children.append(child1)
        parent.children.append(child2)
        parent.children.insert(0, child3)

        assert_that(child1.state_parent).is_same_as(parent)
        assert_that(child2.state_parent).is_same_as(parent)
        assert_that(child3.state_parent).is_same_as(parent)

    def test_auto_parent_does_not_affect_non_state(self) -> None:
        """Non-State items in list are not affected."""

        @state
        class ParentState(State):
            items: Variable[list[str]] = new([])

        parent = ParentState()
        parent.items.append("hello")
        parent.items.append("world")

        # Should not raise - non-State items just get added normally
        assert_that(parent.items.value).is_equal_to(["hello", "world"])
