# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownLambdaType=false
# pyright: reportCallIssue=false
# pyright: reportArgumentType=false
"""Tests for State - QtPie primitive for reactive state without Qt dependencies."""

from assertpy import assert_that
from observant import Observable

from qtpie import State, Variable, new, state


class TestStateBasics:
    """Test basic State functionality."""

    def test_state_with_variable(self) -> None:
        """State can host a Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)

        s = MyState()
        assert_that(s.count.value).is_equal_to(0)
        s.count.value = 5
        assert_that(s.count.value).is_equal_to(5)

    def test_state_variable_with_initial_value(self) -> None:
        """Variable can have initial value via new()."""

        @state
        class MyState(State):
            name: Variable[str] = new("default")

        s = MyState()
        assert_that(s.name.value).is_equal_to("default")

    def test_state_multiple_variables(self) -> None:
        """State can host multiple Variables."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)
            name: Variable[str] = new("")
            active: Variable[bool] = new(False)

        s = MyState()
        assert_that(s.count.value).is_equal_to(0)
        assert_that(s.name.value).is_equal_to("")
        assert_that(s.active.value).is_false()

    def test_state_variable_is_reactive(self) -> None:
        """Variable changes trigger callbacks."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)

        s = MyState()
        received: list[int] = []

        # Subscribe to the underlying observable
        s.count.observable.on_change(lambda v: received.append(v))

        s.count.value = 1
        s.count.value = 2
        s.count.value = 3

        assert_that(received).is_equal_to([1, 2, 3])

    def test_state_per_instance_variables(self) -> None:
        """Each State instance has its own Variables."""

        @state
        class MyState(State):
            value: Variable[int] = new(0)

        s1 = MyState()
        s2 = MyState()

        s1.value.value = 10
        s2.value.value = 20

        assert_that(s1.value.value).is_equal_to(10)
        assert_that(s2.value.value).is_equal_to(20)


class TestStateSetup:
    """Test __setup__ lifecycle hook on State."""

    def test_setup_is_called(self) -> None:
        """__setup__ is called after __init__."""
        calls: list[str] = []

        @state
        class MyState(State):
            count: Variable[int] = new(0)

            def __setup__(self) -> None:
                calls.append("setup")

        MyState()
        assert_that(calls).is_equal_to(["setup"])

    def test_setup_can_access_variables(self) -> None:
        """__setup__ can access Variables."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)
            doubled: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.doubled.value = self.count.value * 2

        s = MyState(count=5)
        assert_that(s.doubled.value).is_equal_to(10)

    def test_setup_called_after_constructor_kwargs_applied(self) -> None:
        """__setup__ sees constructor-provided values."""
        seen_values: list[int] = []

        @state
        class MyState(State):
            count: Variable[int] = new(0)

            def __setup__(self) -> None:
                seen_values.append(self.count.value)

        MyState(count=42)
        assert_that(seen_values).is_equal_to([42])


class TestStateConstructorKwargs:
    """Test passing values to State via constructor."""

    def test_pass_static_value(self) -> None:
        """Can pass static value to Variable via constructor."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)

        s = MyState(count=42)
        assert_that(s.count.value).is_equal_to(42)

    def test_pass_multiple_values(self) -> None:
        """Can pass multiple Variable values in constructor."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)
            name: Variable[str] = new("")

        s = MyState(count=42, name="hello")
        assert_that(s.count.value).is_equal_to(42)
        assert_that(s.name.value).is_equal_to("hello")

    def test_partial_override(self) -> None:
        """Can override some Variables while leaving others at default."""

        @state
        class MyState(State):
            count: Variable[int] = new(10)
            name: Variable[str] = new("default")

        s = MyState(count=99)
        assert_that(s.count.value).is_equal_to(99)
        assert_that(s.name.value).is_equal_to("default")

    def test_pass_observable(self) -> None:
        """Passing Observable shares it with the Variable."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)

        external: Observable[int] = Observable(42)
        s = MyState(count=external)

        assert_that(s.count.value).is_equal_to(42)

        # External change syncs to state
        external.set(100)
        assert_that(s.count.value).is_equal_to(100)

        # State change syncs back to external
        s.count.value = 50
        assert_that(external.get()).is_equal_to(50)

    def test_pass_variable(self) -> None:
        """Passing Variable shares the underlying Observable."""

        @state
        class MyState(State):
            count: Variable[int] = new(0)

        s1 = MyState()
        s1.count.value = 42

        s2 = MyState(count=s1.count)
        assert_that(s2.count.value).is_equal_to(42)

        # Changes sync both ways
        s1.count.value = 100
        assert_that(s2.count.value).is_equal_to(100)

        s2.count.value = 200
        assert_that(s1.count.value).is_equal_to(200)


class TestStateBareVariables:
    """Test bare Variable[T] (no = new()) on State."""

    def test_bare_variable_receives_static_value(self) -> None:
        """Bare Variable receives static value from constructor."""

        @state
        class MyState(State):
            kind: Variable[str]  # Bare - no = new()

        s = MyState(kind="Collection")
        assert_that(s.kind.value).is_equal_to("Collection")

    def test_bare_variable_receives_observable(self) -> None:
        """Bare Variable receives Observable and shares it."""

        @state
        class MyState(State):
            kind: Variable[str]  # Bare

        external: Observable[str] = Observable("Initial")
        s = MyState(kind=external)

        assert_that(s.kind.value).is_equal_to("Initial")

        # Verify bidirectional sync
        external.set("Changed")
        assert_that(s.kind.value).is_equal_to("Changed")

        s.kind.value = "FromState"
        assert_that(external.get()).is_equal_to("FromState")

    def test_bare_variable_receives_variable(self) -> None:
        """Bare Variable receives another Variable and shares Observable."""

        @state
        class MyState(State):
            kind: Variable[str]  # Bare

        # Create first instance with a value
        s1 = MyState(kind="First")

        # Create second instance sharing the first's Variable
        s2 = MyState(kind=s1.kind)

        assert_that(s2.kind.value).is_equal_to("First")

        # Bidirectional sync
        s1.kind.value = "UpdatedFromFirst"
        assert_that(s2.kind.value).is_equal_to("UpdatedFromFirst")

        s2.kind.value = "UpdatedFromSecond"
        assert_that(s1.kind.value).is_equal_to("UpdatedFromSecond")

    def test_mix_bare_and_default_variables(self) -> None:
        """Can mix bare Variables and Variables with defaults."""

        @state
        class MyState(State):
            kind: Variable[str]  # Bare - required
            count: Variable[int] = new(0)  # Has default

        s = MyState(kind="Item", count=10)
        assert_that(s.kind.value).is_equal_to("Item")
        assert_that(s.count.value).is_equal_to(10)

    def test_bare_variable_only_required_passed(self) -> None:
        """Bare Variable provided, other with default not passed."""

        @state
        class MyState(State):
            kind: Variable[str]  # Bare - must pass
            count: Variable[int] = new(100)  # Has default

        s = MyState(kind="Request")
        assert_that(s.kind.value).is_equal_to("Request")
        assert_that(s.count.value).is_equal_to(100)


class TestStateDependencyInjection:
    """Test State-to-State dependency injection."""

    def test_state_receives_another_state(self) -> None:
        """State can receive another state as dependency."""

        @state
        class StateA(State):
            count: Variable[int] = new(0)

        @state
        class StateB(State):
            state_a: Variable[StateA]  # Injected

        a = StateA()
        b = StateB(state_a=a)

        # Access the injected state
        assert_that(b.state_a.value).is_same_as(a)

        # Changes on A reflect on B's reference
        a.count.value = 42
        assert_that(b.state_a.value.count.value).is_equal_to(42)

    def test_multiple_states_share_dependency(self) -> None:
        """Multiple states can share the same dependency."""

        @state
        class ConfigState(State):
            theme: Variable[str] = new("dark")

        @state
        class ConsumerA(State):
            config: Variable[ConfigState]

        @state
        class ConsumerB(State):
            config: Variable[ConfigState]

        config = ConfigState()
        consumer_a = ConsumerA(config=config)
        consumer_b = ConsumerB(config=config)

        # Both consumers see the same config
        assert_that(consumer_a.config.value).is_same_as(config)
        assert_that(consumer_b.config.value).is_same_as(config)

        # Changes propagate to all consumers
        config.theme.value = "light"
        assert_that(consumer_a.config.value.theme.value).is_equal_to("light")
        assert_that(consumer_b.config.value.theme.value).is_equal_to("light")


class TestStateListVariable:
    """Test Variable[list[T]] on State."""

    def test_state_with_list_variable(self) -> None:
        """State can host a list Variable."""

        @state
        class MyState(State):
            items: Variable[list[str]] = new([])

        s = MyState()
        assert_that(s.items.value).is_equal_to([])

        s.items.append("a")
        s.items.append("b")
        assert_that(s.items.value).is_equal_to(["a", "b"])

    def test_state_list_initial_value(self) -> None:
        """State list Variable can have initial items."""

        @state
        class MyState(State):
            items: Variable[list[str]] = new(["a", "b", "c"])

        s = MyState()
        assert_that(s.items.value).is_equal_to(["a", "b", "c"])

    def test_state_list_operations(self) -> None:
        """State list Variable supports standard list operations."""

        @state
        class MyState(State):
            items: Variable[list[int]] = new([1, 2, 3])

        s = MyState()

        s.items.remove(2)
        assert_that(s.items.value).is_equal_to([1, 3])

        s.items.insert(1, 99)
        assert_that(s.items.value).is_equal_to([1, 99, 3])

        s.items.clear()
        assert_that(s.items.value).is_equal_to([])


class TestStateDictVariable:
    """Test Variable[dict[K, V]] on State."""

    def test_state_with_dict_variable(self) -> None:
        """State can host a dict Variable."""

        @state
        class MyState(State):
            config: Variable[dict[str, int]] = new({})

        s = MyState()
        assert_that(s.config.value).is_equal_to({})

        s.config["a"] = 1
        s.config["b"] = 2
        assert_that(s.config.value).is_equal_to({"a": 1, "b": 2})

    def test_state_dict_initial_value(self) -> None:
        """State dict Variable can have initial items."""

        @state
        class MyState(State):
            config: Variable[dict[str, str]] = new({"theme": "dark"})

        s = MyState()
        assert_that(s.config.value).is_equal_to({"theme": "dark"})


class TestStateOnChangeCallback:
    """Test onChange callback for Variable[T] on State."""

    def test_on_change_callback_fires(self) -> None:
        """onChange callback fires when Variable value changes."""
        calls: list[int] = []

        @state
        class MyState(State):
            count: Variable[int] = new(0, onChange="_on_count_changed")

            def _on_count_changed(self) -> None:
                calls.append(self.count.value)

        s = MyState()
        s.count.value = 1
        s.count.value = 2

        assert_that(calls).is_equal_to([1, 2])

    def test_on_change_callback_receives_value(self) -> None:
        """onChange callback can receive the new value as argument."""
        calls: list[str] = []

        @state
        class MyState(State):
            name: Variable[str] = new("", onChange="_on_name_changed")

            def _on_name_changed(self, value: str) -> None:
                calls.append(value)

        s = MyState()
        s.name.value = "hello"
        s.name.value = "world"

        assert_that(calls).is_equal_to(["hello", "world"])

    def test_on_change_with_lambda(self) -> None:
        """onChange can be a lambda or callable."""
        calls: list[int] = []

        @state
        class MyState(State):
            count: Variable[int] = new(0, onChange=lambda v: calls.append(v))

        s = MyState()
        s.count.value = 42

        assert_that(calls).is_equal_to([42])

    def test_on_change_multiple_variables(self) -> None:
        """Multiple Variables can each have their own onChange."""
        count_calls: list[int] = []
        name_calls: list[str] = []

        @state
        class MyState(State):
            count: Variable[int] = new(0, onChange="_on_count")
            name: Variable[str] = new("", onChange="_on_name")

            def _on_count(self, value: int) -> None:
                count_calls.append(value)

            def _on_name(self, value: str) -> None:
                name_calls.append(value)

        s = MyState()
        s.count.value = 10
        s.name.value = "test"
        s.count.value = 20

        assert_that(count_calls).is_equal_to([10, 20])
        assert_that(name_calls).is_equal_to(["test"])

    def test_on_change_list_variable(self) -> None:
        """onChange fires for list Variable mutations."""
        calls: list[int] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new([], onChange="_on_items_changed")

            def _on_items_changed(self) -> None:
                calls.append(len(self.items.value))

        s = MyState()
        s.items.append("a")
        s.items.append("b")
        s.items.remove("a")

        assert_that(calls).is_equal_to([1, 2, 1])

    def test_on_change_dict_variable(self) -> None:
        """onChange fires for dict Variable mutations."""
        calls: list[int] = []

        @state
        class MyState(State):
            config: Variable[dict[str, int]] = new({}, onChange="_on_config_changed")

            def _on_config_changed(self) -> None:
                calls.append(len(self.config.value))

        s = MyState()
        s.config["a"] = 1
        s.config["b"] = 2
        del s.config["a"]

        assert_that(calls).is_equal_to([1, 2, 1])

    def test_on_change_persistence_pattern(self) -> None:
        """State can persist changes via onChange callback."""
        saved_values: list[str] = []

        @state
        class PersistentState(State):
            value: Variable[str] = new("", onChange="_persist")

            def _persist(self) -> None:
                # In real app, this would write to disk
                saved_values.append(self.value.value)

        s = PersistentState()
        s.value.value = "first"
        s.value.value = "second"

        assert_that(saved_values).is_equal_to(["first", "second"])


class TestStateListCallbacks:
    """Test list-specific callbacks (onInsert, onRemove) for Variable[list[T]]."""

    def test_on_insert_callback(self) -> None:
        """onInsert fires when item added to list."""
        inserts: list[tuple[str, int]] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new([], onInsert="_on_insert")

            def _on_insert(self, item: str, index: int) -> None:
                inserts.append((item, index))

        s = MyState()
        s.items.append("a")
        s.items.append("b")
        s.items.insert(0, "first")

        assert_that(inserts).is_equal_to([("a", 0), ("b", 1), ("first", 0)])

    def test_on_insert_item_only(self) -> None:
        """onInsert callback can receive just the item."""
        inserts: list[str] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new([], onInsert="_on_insert")

            def _on_insert(self, item: str) -> None:
                inserts.append(item)

        s = MyState()
        s.items.append("a")
        s.items.append("b")

        assert_that(inserts).is_equal_to(["a", "b"])

    def test_on_remove_callback(self) -> None:
        """onRemove fires when item removed from list."""
        removes: list[tuple[str, int]] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new(["a", "b", "c"], onRemove="_on_remove")

            def _on_remove(self, item: str, index: int) -> None:
                removes.append((item, index))

        s = MyState()
        s.items.remove("b")
        s.items.pop(0)

        assert_that(removes).is_equal_to([("b", 1), ("a", 0)])

    def test_on_remove_item_only(self) -> None:
        """onRemove callback can receive just the item."""
        removes: list[str] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new(["a", "b"], onRemove="_on_remove")

            def _on_remove(self, item: str) -> None:
                removes.append(item)

        s = MyState()
        s.items.remove("a")

        assert_that(removes).is_equal_to(["a"])

    def test_combined_list_callbacks(self) -> None:
        """Can use onChange, onInsert, and onRemove together."""
        events: list[str] = []

        @state
        class MyState(State):
            items: Variable[list[str]] = new(
                [],
                onChange="_on_change",
                onInsert="_on_insert",
                onRemove="_on_remove",
            )

            def _on_change(self) -> None:
                events.append("change")

            def _on_insert(self, item: str) -> None:
                events.append(f"insert:{item}")

            def _on_remove(self, item: str) -> None:
                events.append(f"remove:{item}")

        s = MyState()
        s.items.append("a")
        s.items.remove("a")

        # Both specific and generic callbacks fire
        assert_that(events).contains("change", "insert:a", "remove:a")


class TestStateSetCallbacks:
    """Test set-specific callbacks (onAdd, onRemove) for Variable[set[T]]."""

    def test_on_add_callback(self) -> None:
        """onAdd fires when item added to set."""
        adds: list[str] = []

        @state
        class MyState(State):
            tags: Variable[set[str]] = new(set(), onAdd="_on_add")

            def _on_add(self, item: str) -> None:
                adds.append(item)

        s = MyState()
        s.tags.add("python")
        s.tags.add("qtpie")

        assert_that(adds).is_equal_to(["python", "qtpie"])

    def test_on_remove_callback_set(self) -> None:
        """onRemove fires when item removed from set."""
        removes: list[str] = []

        @state
        class MyState(State):
            tags: Variable[set[str]] = new({"a", "b"}, onRemove="_on_remove")

            def _on_remove(self, item: str) -> None:
                removes.append(item)

        s = MyState()
        s.tags.discard("a")

        assert_that(removes).is_equal_to(["a"])

    def test_combined_set_callbacks(self) -> None:
        """Can use onChange, onAdd, and onRemove together."""
        events: list[str] = []

        @state
        class MyState(State):
            tags: Variable[set[str]] = new(
                set(),
                onChange="_on_change",
                onAdd="_on_add",
                onRemove="_on_remove",
            )

            def _on_change(self) -> None:
                events.append("change")

            def _on_add(self, item: str) -> None:
                events.append(f"add:{item}")

            def _on_remove(self, item: str) -> None:
                events.append(f"remove:{item}")

        s = MyState()
        s.tags.add("x")
        s.tags.discard("x")

        assert_that(events).contains("change", "add:x", "remove:x")


class TestStateDictCallbacks:
    """Test dict-specific callbacks (onSet, onRemove) for Variable[dict[K,V]]."""

    def test_on_set_callback(self) -> None:
        """onSet fires when key is set in dict."""
        sets: list[tuple[str, int]] = []

        @state
        class MyState(State):
            config: Variable[dict[str, int]] = new({}, onSet="_on_set")

            def _on_set(self, key: str, value: int) -> None:
                sets.append((key, value))

        s = MyState()
        s.config["a"] = 1
        s.config["b"] = 2

        assert_that(sets).is_equal_to([("a", 1), ("b", 2)])

    def test_on_set_key_only(self) -> None:
        """onSet callback can receive just the key."""
        keys: list[str] = []

        @state
        class MyState(State):
            config: Variable[dict[str, int]] = new({}, onSet="_on_set")

            def _on_set(self, key: str) -> None:
                keys.append(key)

        s = MyState()
        s.config["x"] = 10
        s.config["y"] = 20

        assert_that(keys).is_equal_to(["x", "y"])

    def test_on_remove_callback_dict(self) -> None:
        """onRemove fires when key is removed from dict."""
        removes: list[tuple[str, int]] = []

        @state
        class MyState(State):
            config: Variable[dict[str, int]] = new({"a": 1, "b": 2}, onRemove="_on_remove")

            def _on_remove(self, key: str, value: int) -> None:
                removes.append((key, value))

        s = MyState()
        del s.config["a"]

        assert_that(removes).is_equal_to([("a", 1)])

    def test_combined_dict_callbacks(self) -> None:
        """Can use onChange, onSet, and onRemove together."""
        events: list[str] = []

        @state
        class MyState(State):
            config: Variable[dict[str, int]] = new(
                {},
                onChange="_on_change",
                onSet="_on_set",
                onRemove="_on_remove",
            )

            def _on_change(self) -> None:
                events.append("change")

            def _on_set(self, key: str, value: int) -> None:
                events.append(f"set:{key}={value}")

            def _on_remove(self, key: str, value: int) -> None:
                events.append(f"remove:{key}")

        s = MyState()
        s.config["x"] = 10
        del s.config["x"]

        assert_that(events).contains("change", "set:x=10", "remove:x")


class TestStateEventNewOn:
    """Test Event[T] = new(on=...) syntax for State."""

    def test_event_new_on_string_handler(self) -> None:
        """Event = new(on="method_name") connects to method."""
        from qtpie import Event

        calls: list[bool] = []

        @state
        class MyState(State):
            on_save: Event = new(on="_on_save")

            def _on_save(self) -> None:
                calls.append(True)

        s = MyState()
        s.on_save.emit()

        assert_that(calls).is_equal_to([True])

    def test_event_new_on_typed_handler(self) -> None:
        """Event[int] = new(on="method_name") passes args to method."""
        from qtpie import Event

        calls: list[int] = []

        @state
        class MyState(State):
            on_value: Event[int] = new(on="_on_value")

            def _on_value(self, x: int) -> None:
                calls.append(x)

        s = MyState()
        s.on_value.emit(42)

        assert_that(calls).is_equal_to([42])

    def test_event_new_on_lambda(self) -> None:
        """Event = new(on=lambda) connects lambda handler."""
        from qtpie import Event

        calls: list[bool] = []

        @state
        class MyState(State):
            on_save: Event = new(on=lambda: calls.append(True))

        s = MyState()
        s.on_save.emit()

        assert_that(calls).is_equal_to([True])

    def test_event_new_on_lambda_with_args(self) -> None:
        """Event[int] = new(on=lambda x: ...) passes args to lambda."""
        from qtpie import Event

        calls: list[int] = []

        @state
        class MyState(State):
            on_value: Event[int] = new(on=lambda x: calls.append(x))

        s = MyState()
        s.on_value.emit(99)

        assert_that(calls).is_equal_to([99])

    def test_event_new_on_expression(self) -> None:
        """Event = new(on="{method()}") connects via expression."""
        from qtpie import Event

        calls: list[bool] = []

        @state
        class MyState(State):
            on_save: Event = new(on="{_log()}")

            def _log(self) -> None:
                calls.append(True)

        s = MyState()
        s.on_save.emit()

        assert_that(calls).is_equal_to([True])

    def test_event_new_on_tuple_args(self) -> None:
        """Event[tuple[int, str]] = new(on="handler") passes multiple args."""
        from qtpie import Event

        calls: list[tuple[int, str]] = []

        @state
        class MyState(State):
            on_data: Event[tuple[int, str]] = new(on="_on_data")

            def _on_data(self, num: int, text: str) -> None:
                calls.append((num, text))

        s = MyState()
        s.on_data.emit(10, "test")

        assert_that(calls).is_equal_to([(10, "test")])

    def test_event_new_on_multiple_events(self) -> None:
        """Multiple Event = new(on=...) fields work together."""
        from qtpie import Event

        first_calls: list[bool] = []
        second_calls: list[int] = []

        @state
        class MyState(State):
            on_first: Event = new(on="_on_first")
            on_second: Event[int] = new(on="_on_second")

            def _on_first(self) -> None:
                first_calls.append(True)

            def _on_second(self, x: int) -> None:
                second_calls.append(x)

        s = MyState()
        s.on_first.emit()
        s.on_second.emit(123)

        assert_that(first_calls).is_equal_to([True])
        assert_that(second_calls).is_equal_to([123])

    def test_event_new_on_coexists_with_decorator_wiring(self) -> None:
        """Event new(on=...) and decorator wiring can coexist."""
        from qtpie import Event

        new_calls: list[str] = []
        decorator_calls: list[str] = []

        @state(on_decorator="_on_decorator")
        class MyState(State):
            on_new: Event = new(on="_on_new")
            on_decorator: Event

            def _on_new(self) -> None:
                new_calls.append("new")

            def _on_decorator(self) -> None:
                decorator_calls.append("decorator")

        s = MyState()
        s.on_new.emit()
        s.on_decorator.emit()

        assert_that(new_calls).is_equal_to(["new"])
        assert_that(decorator_calls).is_equal_to(["decorator"])
