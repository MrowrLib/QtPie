# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownLambdaType=false
# pyright: reportCallIssue=false
# pyright: reportArgumentType=false
"""Tests for Service - QtPie primitive for business logic without Qt dependencies."""

from assertpy import assert_that
from observant import Observable

from qtpie import Service, Variable, new, service


class TestServiceBasics:
    """Test basic Service functionality."""

    def test_service_with_variable(self) -> None:
        """Service can host a Variable."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

        svc = MyService()
        assert_that(svc.count.value).is_equal_to(0)
        svc.count.value = 5
        assert_that(svc.count.value).is_equal_to(5)

    def test_service_variable_with_initial_value(self) -> None:
        """Variable can have initial value via new()."""

        @service
        class MyService(Service):
            name: Variable[str] = new("default")

        svc = MyService()
        assert_that(svc.name.value).is_equal_to("default")

    def test_service_multiple_variables(self) -> None:
        """Service can host multiple Variables."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)
            name: Variable[str] = new("")
            active: Variable[bool] = new(False)

        svc = MyService()
        assert_that(svc.count.value).is_equal_to(0)
        assert_that(svc.name.value).is_equal_to("")
        assert_that(svc.active.value).is_false()

    def test_service_variable_is_reactive(self) -> None:
        """Variable changes trigger callbacks."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

        svc = MyService()
        received: list[int] = []

        # Subscribe to the underlying observable
        svc.count.observable.on_change(lambda v: received.append(v))

        svc.count.value = 1
        svc.count.value = 2
        svc.count.value = 3

        assert_that(received).is_equal_to([1, 2, 3])

    def test_service_per_instance_variables(self) -> None:
        """Each Service instance has its own Variables."""

        @service
        class MyService(Service):
            value: Variable[int] = new(0)

        svc1 = MyService()
        svc2 = MyService()

        svc1.value.value = 10
        svc2.value.value = 20

        assert_that(svc1.value.value).is_equal_to(10)
        assert_that(svc2.value.value).is_equal_to(20)


class TestServiceSetup:
    """Test __setup__ lifecycle hook on Service."""

    def test_setup_is_called(self) -> None:
        """__setup__ is called after __init__."""
        calls: list[str] = []

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

            def __setup__(self) -> None:
                calls.append("setup")

        MyService()
        assert_that(calls).is_equal_to(["setup"])

    def test_setup_can_access_variables(self) -> None:
        """__setup__ can access Variables."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)
            doubled: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.doubled.value = self.count.value * 2

        svc = MyService(count=5)
        assert_that(svc.doubled.value).is_equal_to(10)

    def test_setup_called_after_constructor_kwargs_applied(self) -> None:
        """__setup__ sees constructor-provided values."""
        seen_values: list[int] = []

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

            def __setup__(self) -> None:
                seen_values.append(self.count.value)

        MyService(count=42)
        assert_that(seen_values).is_equal_to([42])


class TestServiceConstructorKwargs:
    """Test passing values to Service via constructor."""

    def test_pass_static_value(self) -> None:
        """Can pass static value to Variable via constructor."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

        svc = MyService(count=42)
        assert_that(svc.count.value).is_equal_to(42)

    def test_pass_multiple_values(self) -> None:
        """Can pass multiple Variable values in constructor."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)
            name: Variable[str] = new("")

        svc = MyService(count=42, name="hello")
        assert_that(svc.count.value).is_equal_to(42)
        assert_that(svc.name.value).is_equal_to("hello")

    def test_partial_override(self) -> None:
        """Can override some Variables while leaving others at default."""

        @service
        class MyService(Service):
            count: Variable[int] = new(10)
            name: Variable[str] = new("default")

        svc = MyService(count=99)
        assert_that(svc.count.value).is_equal_to(99)
        assert_that(svc.name.value).is_equal_to("default")

    def test_pass_observable(self) -> None:
        """Passing Observable shares it with the Variable."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

        external: Observable[int] = Observable(42)
        svc = MyService(count=external)

        assert_that(svc.count.value).is_equal_to(42)

        # External change syncs to service
        external.set(100)
        assert_that(svc.count.value).is_equal_to(100)

        # Service change syncs back to external
        svc.count.value = 50
        assert_that(external.get()).is_equal_to(50)

    def test_pass_variable(self) -> None:
        """Passing Variable shares the underlying Observable."""

        @service
        class MyService(Service):
            count: Variable[int] = new(0)

        svc1 = MyService()
        svc1.count.value = 42

        svc2 = MyService(count=svc1.count)
        assert_that(svc2.count.value).is_equal_to(42)

        # Changes sync both ways
        svc1.count.value = 100
        assert_that(svc2.count.value).is_equal_to(100)

        svc2.count.value = 200
        assert_that(svc1.count.value).is_equal_to(200)


class TestServiceBareVariables:
    """Test bare Variable[T] (no = new()) on Services."""

    def test_bare_variable_receives_static_value(self) -> None:
        """Bare Variable receives static value from constructor."""

        @service
        class MyService(Service):
            kind: Variable[str]  # Bare - no = new()

        svc = MyService(kind="Collection")
        assert_that(svc.kind.value).is_equal_to("Collection")

    def test_bare_variable_receives_observable(self) -> None:
        """Bare Variable receives Observable and shares it."""

        @service
        class MyService(Service):
            kind: Variable[str]  # Bare

        external: Observable[str] = Observable("Initial")
        svc = MyService(kind=external)

        assert_that(svc.kind.value).is_equal_to("Initial")

        # Verify bidirectional sync
        external.set("Changed")
        assert_that(svc.kind.value).is_equal_to("Changed")

        svc.kind.value = "FromService"
        assert_that(external.get()).is_equal_to("FromService")

    def test_bare_variable_receives_variable(self) -> None:
        """Bare Variable receives another Variable and shares Observable."""

        @service
        class MyService(Service):
            kind: Variable[str]  # Bare

        # Create first instance with a value
        svc1 = MyService(kind="First")

        # Create second instance sharing the first's Variable
        svc2 = MyService(kind=svc1.kind)

        assert_that(svc2.kind.value).is_equal_to("First")

        # Bidirectional sync
        svc1.kind.value = "UpdatedFromFirst"
        assert_that(svc2.kind.value).is_equal_to("UpdatedFromFirst")

        svc2.kind.value = "UpdatedFromSecond"
        assert_that(svc1.kind.value).is_equal_to("UpdatedFromSecond")

    def test_mix_bare_and_default_variables(self) -> None:
        """Can mix bare Variables and Variables with defaults."""

        @service
        class MyService(Service):
            kind: Variable[str]  # Bare - required
            count: Variable[int] = new(0)  # Has default

        svc = MyService(kind="Item", count=10)
        assert_that(svc.kind.value).is_equal_to("Item")
        assert_that(svc.count.value).is_equal_to(10)

    def test_bare_variable_only_required_passed(self) -> None:
        """Bare Variable provided, other with default not passed."""

        @service
        class MyService(Service):
            kind: Variable[str]  # Bare - must pass
            count: Variable[int] = new(100)  # Has default

        svc = MyService(kind="Request")
        assert_that(svc.kind.value).is_equal_to("Request")
        assert_that(svc.count.value).is_equal_to(100)


class TestServiceDependencyInjection:
    """Test Service-to-Service dependency injection."""

    def test_service_receives_another_service(self) -> None:
        """Service can receive another service as dependency."""

        @service
        class ServiceA(Service):
            count: Variable[int] = new(0)

        @service
        class ServiceB(Service):
            service_a: Variable[ServiceA]  # Injected

        a = ServiceA()
        b = ServiceB(service_a=a)

        # Access the injected service
        assert_that(b.service_a.value).is_same_as(a)

        # Changes on A reflect on B's reference
        a.count.value = 42
        assert_that(b.service_a.value.count.value).is_equal_to(42)

    def test_multiple_services_share_dependency(self) -> None:
        """Multiple services can share the same dependency."""

        @service
        class ConfigService(Service):
            theme: Variable[str] = new("dark")

        @service
        class ConsumerA(Service):
            config: Variable[ConfigService]

        @service
        class ConsumerB(Service):
            config: Variable[ConfigService]

        config = ConfigService()
        consumer_a = ConsumerA(config=config)
        consumer_b = ConsumerB(config=config)

        # Both consumers see the same config
        assert_that(consumer_a.config.value).is_same_as(config)
        assert_that(consumer_b.config.value).is_same_as(config)

        # Changes propagate to all consumers
        config.theme.value = "light"
        assert_that(consumer_a.config.value.theme.value).is_equal_to("light")
        assert_that(consumer_b.config.value.theme.value).is_equal_to("light")


class TestServiceListVariable:
    """Test Variable[list[T]] on Services."""

    def test_service_with_list_variable(self) -> None:
        """Service can host a list Variable."""

        @service
        class MyService(Service):
            items: Variable[list[str]] = new([])

        svc = MyService()
        assert_that(svc.items.value).is_equal_to([])

        svc.items.append("a")
        svc.items.append("b")
        assert_that(svc.items.value).is_equal_to(["a", "b"])

    def test_service_list_initial_value(self) -> None:
        """Service list Variable can have initial items."""

        @service
        class MyService(Service):
            items: Variable[list[str]] = new(["a", "b", "c"])

        svc = MyService()
        assert_that(svc.items.value).is_equal_to(["a", "b", "c"])

    def test_service_list_operations(self) -> None:
        """Service list Variable supports standard list operations."""

        @service
        class MyService(Service):
            items: Variable[list[int]] = new([1, 2, 3])

        svc = MyService()

        svc.items.remove(2)
        assert_that(svc.items.value).is_equal_to([1, 3])

        svc.items.insert(1, 99)
        assert_that(svc.items.value).is_equal_to([1, 99, 3])

        svc.items.clear()
        assert_that(svc.items.value).is_equal_to([])


class TestServiceDictVariable:
    """Test Variable[dict[K, V]] on Services."""

    def test_service_with_dict_variable(self) -> None:
        """Service can host a dict Variable."""

        @service
        class MyService(Service):
            config: Variable[dict[str, int]] = new({})

        svc = MyService()
        assert_that(svc.config.value).is_equal_to({})

        svc.config["a"] = 1
        svc.config["b"] = 2
        assert_that(svc.config.value).is_equal_to({"a": 1, "b": 2})

    def test_service_dict_initial_value(self) -> None:
        """Service dict Variable can have initial items."""

        @service
        class MyService(Service):
            config: Variable[dict[str, str]] = new({"theme": "dark"})

        svc = MyService()
        assert_that(svc.config.value).is_equal_to({"theme": "dark"})


class TestServiceOnChangeCallback:
    """Test onChange callback for Variable[T] on Services."""

    def test_on_change_callback_fires(self) -> None:
        """onChange callback fires when Variable value changes."""
        calls: list[int] = []

        @service
        class MyService(Service):
            count: Variable[int] = new(0, onChange="_on_count_changed")

            def _on_count_changed(self) -> None:
                calls.append(self.count.value)

        svc = MyService()
        svc.count.value = 1
        svc.count.value = 2

        assert_that(calls).is_equal_to([1, 2])

    def test_on_change_callback_receives_value(self) -> None:
        """onChange callback can receive the new value as argument."""
        calls: list[str] = []

        @service
        class MyService(Service):
            name: Variable[str] = new("", onChange="_on_name_changed")

            def _on_name_changed(self, value: str) -> None:
                calls.append(value)

        svc = MyService()
        svc.name.value = "hello"
        svc.name.value = "world"

        assert_that(calls).is_equal_to(["hello", "world"])

    def test_on_change_with_lambda(self) -> None:
        """onChange can be a lambda or callable."""
        calls: list[int] = []

        @service
        class MyService(Service):
            count: Variable[int] = new(0, onChange=lambda v: calls.append(v))

        svc = MyService()
        svc.count.value = 42

        assert_that(calls).is_equal_to([42])

    def test_on_change_multiple_variables(self) -> None:
        """Multiple Variables can each have their own onChange."""
        count_calls: list[int] = []
        name_calls: list[str] = []

        @service
        class MyService(Service):
            count: Variable[int] = new(0, onChange="_on_count")
            name: Variable[str] = new("", onChange="_on_name")

            def _on_count(self, value: int) -> None:
                count_calls.append(value)

            def _on_name(self, value: str) -> None:
                name_calls.append(value)

        svc = MyService()
        svc.count.value = 10
        svc.name.value = "test"
        svc.count.value = 20

        assert_that(count_calls).is_equal_to([10, 20])
        assert_that(name_calls).is_equal_to(["test"])

    def test_on_change_list_variable(self) -> None:
        """onChange fires for list Variable mutations."""
        calls: list[int] = []

        @service
        class MyService(Service):
            items: Variable[list[str]] = new([], onChange="_on_items_changed")

            def _on_items_changed(self) -> None:
                calls.append(len(self.items.value))

        svc = MyService()
        svc.items.append("a")
        svc.items.append("b")
        svc.items.remove("a")

        assert_that(calls).is_equal_to([1, 2, 1])

    def test_on_change_dict_variable(self) -> None:
        """onChange fires for dict Variable mutations."""
        calls: list[int] = []

        @service
        class MyService(Service):
            config: Variable[dict[str, int]] = new({}, onChange="_on_config_changed")

            def _on_config_changed(self) -> None:
                calls.append(len(self.config.value))

        svc = MyService()
        svc.config["a"] = 1
        svc.config["b"] = 2
        del svc.config["a"]

        assert_that(calls).is_equal_to([1, 2, 1])

    def test_on_change_persistence_pattern(self) -> None:
        """Service can persist changes via onChange callback."""
        saved_values: list[str] = []

        @service
        class PersistentService(Service):
            value: Variable[str] = new("", onChange="_persist")

            def _persist(self) -> None:
                # In real app, this would write to disk
                saved_values.append(self.value.value)

        svc = PersistentService()
        svc.value.value = "first"
        svc.value.value = "second"

        assert_that(saved_values).is_equal_to(["first", "second"])


class TestServiceListCallbacks:
    """Test list-specific callbacks (onInsert, onRemove) for Variable[list[T]]."""

    def test_on_insert_callback(self) -> None:
        """onInsert fires when item added to list."""
        inserts: list[tuple[str, int]] = []

        @service
        class MyService(Service):
            items: Variable[list[str]] = new([], onInsert="_on_insert")

            def _on_insert(self, item: str, index: int) -> None:
                inserts.append((item, index))

        svc = MyService()
        svc.items.append("a")
        svc.items.append("b")
        svc.items.insert(0, "first")

        assert_that(inserts).is_equal_to([("a", 0), ("b", 1), ("first", 0)])

    def test_on_insert_item_only(self) -> None:
        """onInsert callback can receive just the item."""
        inserts: list[str] = []

        @service
        class MyService(Service):
            items: Variable[list[str]] = new([], onInsert="_on_insert")

            def _on_insert(self, item: str) -> None:
                inserts.append(item)

        svc = MyService()
        svc.items.append("a")
        svc.items.append("b")

        assert_that(inserts).is_equal_to(["a", "b"])

    def test_on_remove_callback(self) -> None:
        """onRemove fires when item removed from list."""
        removes: list[tuple[str, int]] = []

        @service
        class MyService(Service):
            items: Variable[list[str]] = new(["a", "b", "c"], onRemove="_on_remove")

            def _on_remove(self, item: str, index: int) -> None:
                removes.append((item, index))

        svc = MyService()
        svc.items.remove("b")
        svc.items.pop(0)

        assert_that(removes).is_equal_to([("b", 1), ("a", 0)])

    def test_on_remove_item_only(self) -> None:
        """onRemove callback can receive just the item."""
        removes: list[str] = []

        @service
        class MyService(Service):
            items: Variable[list[str]] = new(["a", "b"], onRemove="_on_remove")

            def _on_remove(self, item: str) -> None:
                removes.append(item)

        svc = MyService()
        svc.items.remove("a")

        assert_that(removes).is_equal_to(["a"])

    def test_combined_list_callbacks(self) -> None:
        """Can use onChange, onInsert, and onRemove together."""
        events: list[str] = []

        @service
        class MyService(Service):
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

        svc = MyService()
        svc.items.append("a")
        svc.items.remove("a")

        # Both specific and generic callbacks fire
        assert_that(events).contains("change", "insert:a", "remove:a")


class TestServiceSetCallbacks:
    """Test set-specific callbacks (onAdd, onRemove) for Variable[set[T]]."""

    def test_on_add_callback(self) -> None:
        """onAdd fires when item added to set."""
        adds: list[str] = []

        @service
        class MyService(Service):
            tags: Variable[set[str]] = new(set(), onAdd="_on_add")

            def _on_add(self, item: str) -> None:
                adds.append(item)

        svc = MyService()
        svc.tags.add("python")
        svc.tags.add("qtpie")

        assert_that(adds).is_equal_to(["python", "qtpie"])

    def test_on_remove_callback_set(self) -> None:
        """onRemove fires when item removed from set."""
        removes: list[str] = []

        @service
        class MyService(Service):
            tags: Variable[set[str]] = new({"a", "b"}, onRemove="_on_remove")

            def _on_remove(self, item: str) -> None:
                removes.append(item)

        svc = MyService()
        svc.tags.discard("a")

        assert_that(removes).is_equal_to(["a"])

    def test_combined_set_callbacks(self) -> None:
        """Can use onChange, onAdd, and onRemove together."""
        events: list[str] = []

        @service
        class MyService(Service):
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

        svc = MyService()
        svc.tags.add("x")
        svc.tags.discard("x")

        assert_that(events).contains("change", "add:x", "remove:x")


class TestServiceDictCallbacks:
    """Test dict-specific callbacks (onSet, onRemove) for Variable[dict[K,V]]."""

    def test_on_set_callback(self) -> None:
        """onSet fires when key is set in dict."""
        sets: list[tuple[str, int]] = []

        @service
        class MyService(Service):
            config: Variable[dict[str, int]] = new({}, onSet="_on_set")

            def _on_set(self, key: str, value: int) -> None:
                sets.append((key, value))

        svc = MyService()
        svc.config["a"] = 1
        svc.config["b"] = 2

        assert_that(sets).is_equal_to([("a", 1), ("b", 2)])

    def test_on_set_key_only(self) -> None:
        """onSet callback can receive just the key."""
        keys: list[str] = []

        @service
        class MyService(Service):
            config: Variable[dict[str, int]] = new({}, onSet="_on_set")

            def _on_set(self, key: str) -> None:
                keys.append(key)

        svc = MyService()
        svc.config["x"] = 10
        svc.config["y"] = 20

        assert_that(keys).is_equal_to(["x", "y"])

    def test_on_remove_callback_dict(self) -> None:
        """onRemove fires when key is removed from dict."""
        removes: list[tuple[str, int]] = []

        @service
        class MyService(Service):
            config: Variable[dict[str, int]] = new({"a": 1, "b": 2}, onRemove="_on_remove")

            def _on_remove(self, key: str, value: int) -> None:
                removes.append((key, value))

        svc = MyService()
        del svc.config["a"]

        assert_that(removes).is_equal_to([("a", 1)])

    def test_combined_dict_callbacks(self) -> None:
        """Can use onChange, onSet, and onRemove together."""
        events: list[str] = []

        @service
        class MyService(Service):
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

        svc = MyService()
        svc.config["x"] = 10
        del svc.config["x"]

        assert_that(events).contains("change", "set:x=10", "remove:x")
