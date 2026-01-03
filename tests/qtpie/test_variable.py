# pyright: reportPrivateUsage=false
"""Tests for Variable[T] with new() and @new_fields."""

from assertpy import assert_that

from qtpie import Variable, new, new_fields


class TestVariableWithNewFields:
    """Test Variable fields processed by @new_fields."""

    def test_variable_stores_default(self) -> None:
        """Variable returns default value before any set."""

        @new_fields
        class MyClass:
            _name: Variable[str] = new("default")

        obj = MyClass()
        assert_that(obj._name.value).is_equal_to("default")

    def test_variable_set_and_get(self) -> None:
        """Variable can be set and retrieved."""

        @new_fields
        class MyClass:
            _count: Variable[int] = new(0)

        obj = MyClass()
        obj._count.value = 42
        assert_that(obj._count.value).is_equal_to(42)

    def test_variable_direct_assignment(self) -> None:
        """Direct assignment sets the value."""

        @new_fields
        class MyClass:
            _count: Variable[int] = new(0)

        obj = MyClass()
        obj._count = 42  # Direct assignment (pyright doesn't understand descriptors)  # pyright: ignore[reportAttributeAccessIssue]
        assert_that(obj._count.value).is_equal_to(42)

    def test_variable_per_instance(self) -> None:
        """Each instance has its own value."""

        @new_fields
        class MyClass:
            _value: Variable[int] = new(0)

        a = MyClass()
        b = MyClass()

        a._value.value = 10
        b._value.value = 20

        assert_that(a._value.value).is_equal_to(10)
        assert_that(b._value.value).is_equal_to(20)

    def test_variable_is_reactive(self) -> None:
        """Variable changes trigger callbacks."""

        @new_fields
        class MyClass:
            _name: Variable[str] = new("")

        obj = MyClass()
        received: list[str] = []

        # Access the observable via the Variable instance
        obj._name.observable.on_change(lambda v: received.append(v))

        obj._name.value = "hello"
        obj._name.value = "world"

        assert_that(received).is_equal_to(["hello", "world"])

    def test_variable_returns_variable_instance(self) -> None:
        """Accessing a Variable field returns a Variable instance."""

        @new_fields
        class MyClass:
            _name: Variable[str] = new("test")

        obj = MyClass()
        assert_that(obj._name).is_instance_of(Variable)
        assert_that(obj._name.value).is_equal_to("test")


class TestNewWithNonVariableTypes:
    """Test new() with regular types (not Variable)."""

    def test_new_instantiates_type(self) -> None:
        """new() instantiates the annotated type with args."""

        class Greeter:
            def __init__(self, name: str) -> None:
                self.name = name

        @new_fields
        class MyClass:
            _greeter: Greeter = new("Alice")

        obj = MyClass()
        assert_that(obj._greeter.name).is_equal_to("Alice")

    def test_new_with_kwargs(self) -> None:
        """new() passes kwargs to constructor."""

        class Config:
            def __init__(self, *, host: str, port: int) -> None:
                self.host = host
                self.port = port

        @new_fields
        class MyClass:
            _config: Config = new(host="localhost", port=8080)

        obj = MyClass()
        assert_that(obj._config.host).is_equal_to("localhost")
        assert_that(obj._config.port).is_equal_to(8080)

    def test_mixed_variable_and_regular(self) -> None:
        """Can mix Variable and regular types."""

        class Counter:
            def __init__(self, start: int = 0) -> None:
                self.value = start

        @new_fields
        class MyClass:
            _name: Variable[str] = new("test")
            _counter: Counter = new(start=10)

        obj = MyClass()
        assert_that(obj._name.value).is_equal_to("test")
        assert_that(obj._counter.value).is_equal_to(10)

        obj._name.value = "updated"
        assert_that(obj._name.value).is_equal_to("updated")


class TestVariablePrimitiveDefaults:
    """Test new() with primitive defaults (no default= kwarg needed)."""

    def test_string_default(self) -> None:
        """new('') works without default= for strings."""

        @new_fields
        class MyClass:
            _name: Variable[str] = new("hello")

        obj = MyClass()
        assert_that(obj._name.value).is_equal_to("hello")

    def test_int_default(self) -> None:
        """new(42) works without default= for ints."""

        @new_fields
        class MyClass:
            _count: Variable[int] = new(42)

        obj = MyClass()
        assert_that(obj._count.value).is_equal_to(42)

    def test_float_default(self) -> None:
        """new(3.14) works without default= for floats."""

        @new_fields
        class MyClass:
            _ratio: Variable[float] = new(3.14)

        obj = MyClass()
        assert_that(obj._ratio.value).is_equal_to(3.14)

    def test_bool_default(self) -> None:
        """new(True) works without default= for bools."""

        @new_fields
        class MyClass:
            _enabled: Variable[bool] = new(True)

        obj = MyClass()
        assert_that(obj._enabled.value).is_true()

    def test_default_kwarg_still_works(self) -> None:
        """default= kwarg still works for backwards compatibility."""

        @new_fields
        class MyClass:
            _value: Variable[int] = new(default=99)

        obj = MyClass()
        assert_that(obj._value.value).is_equal_to(99)


class TestNewFieldsIdempotent:
    """Test that @new_fields is idempotent."""

    def test_double_decoration(self) -> None:
        """Applying @new_fields twice doesn't break anything."""

        @new_fields
        @new_fields
        class MyClass:
            _value: Variable[int] = new(0)

        obj = MyClass()
        obj._value.value = 5
        assert_that(obj._value.value).is_equal_to(5)
