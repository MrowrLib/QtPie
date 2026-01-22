# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
"""Tests for State callback expressions with onChange, onInsert, etc."""

from typing import Any

from assertpy import assert_that

from qtpie import State, Variable, new, state
from qtpie.event import Event


class TestOnChangeExpression:
    """Tests for onChange with expression syntax."""

    def test_expression_calls_method(self) -> None:
        """onChange="{handle()}" calls method."""
        calls: list[str] = []

        @state
        class MyState(State):
            value: Variable[str] = new("", onChange="{_on_changed()}")

            def _on_changed(self) -> None:
                calls.append("changed")

        s = MyState()
        s.value.value = "hello"

        assert_that(calls).is_equal_to(["changed"])

    def test_expression_with_args(self) -> None:
        """onChange="{handle(#args)}" passes value to method."""
        received: list[str] = []

        @state
        class MyState(State):
            value: Variable[str] = new("", onChange="{_on_changed(#args)}")

            def _on_changed(self, val: str) -> None:
                received.append(val)

        s = MyState()
        s.value.value = "hello"
        s.value.value = "world"

        assert_that(received).is_equal_to(["hello", "world"])

    def test_expression_emits_event(self) -> None:
        """onChange="{on_save()}" emits an Event."""
        calls: list[str] = []

        @state
        class MyState(State):
            value: Variable[str] = new("", onChange="{on_save()}")
            on_save: Event

        s = MyState()
        s.on_save.connect(lambda: calls.append("saved"))

        s.value.value = "data"

        assert_that(calls).is_equal_to(["saved"])

    def test_expression_emits_event_with_args(self) -> None:
        """onChange="{on_data(#args)}" emits Event with value."""
        received: list[str] = []

        @state
        class MyState(State):
            value: Variable[str] = new("", onChange="{on_data(#args)}")
            on_data: Event[str]

        s = MyState()
        s.on_data.connect(lambda v: received.append(v))

        s.value.value = "hello"

        assert_that(received).is_equal_to(["hello"])

    def test_expression_with_self_placeholder(self) -> None:
        """onChange="{#self.process()}" uses #self for state instance."""
        calls: list[str] = []

        @state
        class MyState(State):
            value: Variable[str] = new("", onChange="{#self.process()}")
            name: str = "TestState"

            def process(self) -> None:
                calls.append(f"process:{self.name}")

        s = MyState()
        s.value.value = "x"

        assert_that(calls).is_equal_to(["process:TestState"])

    def test_expression_accesses_parent_event(self) -> None:
        """Child expression can emit parent's Event."""
        calls: list[str] = []

        @state
        class ChildState(State):
            value: Variable[str] = new("", onChange="{on_parent_save()}")

        @state
        class ParentState(State):
            on_parent_save: Event
            children: Variable[list[Any]] = new([])

        parent = ParentState()
        parent.on_parent_save.connect(lambda: calls.append("parent_saved"))

        child = ChildState()
        parent.children.append(child)

        child.value.value = "data"

        assert_that(calls).is_equal_to(["parent_saved"])

    def test_expression_accesses_parent_method(self) -> None:
        """Child expression can call parent's method."""
        calls: list[str] = []

        @state
        class ChildState(State):
            value: Variable[str] = new("", onChange="{_parent_handler()}")

        @state
        class ParentState(State):
            children: Variable[list[Any]] = new([])

            def _parent_handler(self) -> None:
                calls.append("parent_called")

        parent = ParentState()
        child = ChildState()
        parent.children.append(child)

        child.value.value = "x"

        assert_that(calls).is_equal_to(["parent_called"])


class TestOnInsertExpression:
    """Tests for onInsert with expression syntax."""

    def test_list_insert_expression_calls_method(self) -> None:
        """onInsert="{handle()}" on list calls method."""
        calls: list[str] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new([], onInsert="{_on_add()}")

            def _on_add(self) -> None:
                calls.append("added")

        s = MyState()
        s.items.append("a")
        s.items.append("b")

        assert_that(calls).is_equal_to(["added", "added"])

    def test_list_insert_expression_with_args(self) -> None:
        """onInsert="{handle(#args)}" passes (item, index) to method."""
        received: list[tuple[str, int]] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new([], onInsert="{_on_add(#args)}")

            def _on_add(self, item: str, index: int) -> None:
                received.append((item, index))

        s = MyState()
        s.items.append("first")
        s.items.insert(0, "zeroth")

        assert_that(received).is_equal_to([("first", 0), ("zeroth", 0)])

    def test_list_insert_emits_event(self) -> None:
        """onInsert="{on_item_added()}" emits Event."""
        calls: list[str] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new([], onInsert="{on_item_added()}")
            on_item_added: Event

        s = MyState()
        s.on_item_added.connect(lambda: calls.append("event"))

        s.items.append("x")

        assert_that(calls).is_equal_to(["event"])


class TestOnRemoveExpression:
    """Tests for onRemove with expression syntax."""

    def test_list_remove_expression_calls_method(self) -> None:
        """onRemove="{handle()}" on list calls method."""
        calls: list[str] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new(["a", "b"], onRemove="{_on_removed()}")

            def _on_removed(self) -> None:
                calls.append("removed")

        s = MyState()
        s.items.remove("a")

        assert_that(calls).is_equal_to(["removed"])

    def test_list_remove_expression_with_args(self) -> None:
        """onRemove="{handle(#args)}" passes (item, index) to method."""
        received: list[tuple[str, int]] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new(["a", "b"], onRemove="{_on_removed(#args)}")

            def _on_removed(self, item: str, index: int) -> None:
                received.append((item, index))

        s = MyState()
        s.items.pop(0)

        assert_that(received).is_equal_to([("a", 0)])

    def test_set_remove_expression_with_args(self) -> None:
        """onRemove="{handle(#args)}" on set passes (item,) to method."""
        received: list[str] = []

        @state
        class MyState(State):
            items: Variable[set[str]] = new({"a", "b"}, onRemove="{_on_removed(#args)}")

            def _on_removed(self, item: str) -> None:
                received.append(item)

        s = MyState()
        s.items.discard("a")

        assert_that(received).is_equal_to(["a"])


class TestOnAddExpression:
    """Tests for onAdd with expression syntax (sets only)."""

    def test_set_add_expression_calls_method(self) -> None:
        """onAdd="{handle()}" on set calls method."""
        calls: list[str] = []

        @state
        class MyState(State):
            items: Variable[set[str]] = new(set(), onAdd="{_on_added()}")

            def _on_added(self) -> None:
                calls.append("added")

        s = MyState()
        s.items.add("a")

        assert_that(calls).is_equal_to(["added"])

    def test_set_add_expression_with_args(self) -> None:
        """onAdd="{handle(#args)}" passes (item,) to method."""
        received: list[str] = []

        @state
        class MyState(State):
            items: Variable[set[str]] = new(set(), onAdd="{_on_added(#args)}")

            def _on_added(self, item: str) -> None:
                received.append(item)

        s = MyState()
        s.items.add("hello")

        assert_that(received).is_equal_to(["hello"])


class TestOnSetExpression:
    """Tests for onSet with expression syntax (dicts only)."""

    def test_dict_set_expression_calls_method(self) -> None:
        """onSet="{handle()}" on dict calls method."""
        calls: list[str] = []

        @state
        class MyState(State):
            items: Variable[dict[str, int]] = new({}, onSet="{_on_set()}")

            def _on_set(self) -> None:
                calls.append("set")

        s = MyState()
        s.items["a"] = 1

        assert_that(calls).is_equal_to(["set"])

    def test_dict_set_expression_with_args(self) -> None:
        """onSet="{handle(#args)}" passes (key, value) to method."""
        received: list[tuple[str, int]] = []

        @state
        class MyState(State):
            items: Variable[dict[str, int]] = new({}, onSet="{_on_set(#args)}")

            def _on_set(self, key: str, value: int) -> None:
                received.append((key, value))

        s = MyState()
        s.items["x"] = 42

        assert_that(received).is_equal_to([("x", 42)])


class TestExpressionWithComplexExpressions:
    """Tests for complex expressions in callbacks."""

    def test_expression_with_function_call_and_literal(self) -> None:
        """onChange="{handle('literal', 123)}" works."""
        received: list[tuple[str, int]] = []

        @state
        class MyState(State):
            value: Variable[str] = new("", onChange="{_on_changed('literal', 123)}")

            def _on_changed(self, s: str, n: int) -> None:
                received.append((s, n))

        s = MyState()
        s.value.value = "x"

        assert_that(received).is_equal_to([("literal", 123)])

    def test_expression_accessing_state_variable(self) -> None:
        """onChange="{handle(count)}" can access other Variables."""
        received: list[int] = []

        @state
        class MyState(State):
            count: Variable[int] = new(42)
            trigger: Variable[str] = new("", onChange="{_on_changed(count)}")

            def _on_changed(self, val: int) -> None:
                received.append(val)

        s = MyState()
        s.trigger.value = "go"

        assert_that(received).is_equal_to([42])

    def test_expression_with_math(self) -> None:
        """onChange="{handle(count * 2)}" can do math."""
        received: list[int] = []

        @state
        class MyState(State):
            count: Variable[int] = new(10)
            trigger: Variable[str] = new("", onChange="{_on_changed(count * 2)}")

            def _on_changed(self, val: int) -> None:
                received.append(val)

        s = MyState()
        s.trigger.value = "go"

        assert_that(received).is_equal_to([20])


class TestAssignmentExpressions:
    """Tests for assignment expressions in callbacks (e.g., {count += 1})."""

    def test_simple_assignment_to_variable(self) -> None:
        """onChange="{count = 42}" assigns to Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)
            trigger: Variable[str] = new("", onChange="{count = 42}")

        s = MyState()
        assert_that(s.count.value).is_equal_to(0)
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(42)

    def test_increment_assignment_to_variable(self) -> None:
        """onChange="{count += 1}" increments Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(10)
            trigger: Variable[str] = new("", onChange="{count += 1}")

        s = MyState()
        assert_that(s.count.value).is_equal_to(10)
        s.trigger.value = "a"
        assert_that(s.count.value).is_equal_to(11)
        s.trigger.value = "b"
        assert_that(s.count.value).is_equal_to(12)

    def test_decrement_assignment_to_variable(self) -> None:
        """onChange="{count -= 5}" decrements Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(100)
            trigger: Variable[str] = new("", onChange="{count -= 5}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(95)

    def test_multiply_assignment_to_variable(self) -> None:
        """onChange="{count *= 2}" multiplies Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(3)
            trigger: Variable[str] = new("", onChange="{count *= 2}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(6)

    def test_divide_assignment_to_variable(self) -> None:
        """onChange="{count /= 2}" divides Variable."""

        @state
        class MyState(State):
            count: Variable[float] = new(10.0)
            trigger: Variable[str] = new("", onChange="{count /= 2}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(5.0)

    def test_floor_divide_assignment_to_variable(self) -> None:
        """onChange="{count //= 3}" floor divides Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(10)
            trigger: Variable[str] = new("", onChange="{count //= 3}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(3)

    def test_modulo_assignment_to_variable(self) -> None:
        """onChange="{count %= 3}" applies modulo to Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(10)
            trigger: Variable[str] = new("", onChange="{count %= 3}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(1)

    def test_power_assignment_to_variable(self) -> None:
        """onChange="{count **= 2}" raises Variable to power."""

        @state
        class MyState(State):
            count: Variable[int] = new(3)
            trigger: Variable[str] = new("", onChange="{count **= 2}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.count.value).is_equal_to(9)

    def test_assignment_with_expression(self) -> None:
        """onChange="{result = a + b}" assigns computed value."""

        @state
        class MyState(State):
            a: Variable[int] = new(10)
            b: Variable[int] = new(20)
            result: Variable[int] = new(0)
            trigger: Variable[str] = new("", onChange="{result = a + b}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.result.value).is_equal_to(30)

    def test_assignment_with_method_call(self) -> None:
        """onChange="{result = compute()}" assigns method return value."""

        @state
        class MyState(State):
            result: Variable[int] = new(0)
            trigger: Variable[str] = new("", onChange="{result = _compute()}")

            def _compute(self) -> int:
                return 999

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.result.value).is_equal_to(999)

    def test_bitwise_or_assignment(self) -> None:
        """onChange="{flags |= 4}" applies bitwise OR."""

        @state
        class MyState(State):
            flags: Variable[int] = new(1)
            trigger: Variable[str] = new("", onChange="{flags |= 4}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.flags.value).is_equal_to(5)  # 0b001 | 0b100 = 0b101

    def test_bitwise_and_assignment(self) -> None:
        """onChange="{flags &= 3}" applies bitwise AND."""

        @state
        class MyState(State):
            flags: Variable[int] = new(7)  # 0b111
            trigger: Variable[str] = new("", onChange="{flags &= 3}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s.flags.value).is_equal_to(3)  # 0b111 & 0b011 = 0b011

    def test_assignment_to_underscore_prefixed_variable(self) -> None:
        """onChange="{count += 1}" finds _count Variable."""

        @state
        class MyState(State):
            _count: Variable[int] = new(0)
            trigger: Variable[str] = new("", onChange="{count += 1}")

        s = MyState()
        s.trigger.value = "go"
        assert_that(s._count.value).is_equal_to(1)

    def test_equals_in_string_not_treated_as_assignment(self) -> None:
        """print("x = 1") is NOT an assignment, it's a function call."""
        received: list[str] = []

        @state
        class MyState(State):
            trigger: Variable[str] = new("", onChange='{_log("x = 1")}')

            def _log(self, msg: str) -> None:
                received.append(msg)

        s = MyState()
        s.trigger.value = "go"
        assert_that(received).is_equal_to(["x = 1"])
