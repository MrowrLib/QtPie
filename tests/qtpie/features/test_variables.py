# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for Variable[T] across Widget, Window, and Menu.

Pyright ignores: pytest.param() returns Any, causing type cascade issues.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, WIDGET_CLASS_TYPES, create_and_track


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableCreation:
    """Variable[T] creation works across all class types."""

    def test_variable_int_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[int] stores default value."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.value).is_equal_to(0)

    def test_variable_str_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str] stores default value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("hello")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.value).is_equal_to("hello")

    def test_variable_bool_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[bool] stores default value."""

        @decorator
        class TestClass(base_class):
            _enabled: Variable[bool] = new(True)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._enabled.value).is_true()


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableModification:
    """Variable[T] modification works across all class types."""

    def test_variable_set_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable.value can be set."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count.value = 42
        assert_that(instance._count.value).is_equal_to(42)

    def test_variable_augmented_assignment(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports += operator."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count += 5
        assert_that(instance._count.value).is_equal_to(15)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVariableWithWidget:
    """Variable[T, W] inline widgets - only for Widget/Window (not Menu)."""

    def test_variable_with_label(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, QLabel] creates label bound to value."""

        @decorator
        class TestClass(base_class):
            _message: Variable[str, QLabel] = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)

        # Widget was created
        assert_that(instance._message.widget).is_instance_of(QLabel)
        # Initial value displayed
        assert_that(instance._message.widget.text()).is_equal_to("Hello")

        # Value change updates widget
        instance._message.value = "World"
        assert_that(instance._message.widget.text()).is_equal_to("World")

    def test_variable_with_lineedit(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, QLineEdit] creates editable input."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._name.widget).is_instance_of(QLineEdit)

        # Typing in widget updates value
        instance._name.widget.setText("typed text")
        assert_that(instance._name.value).is_equal_to("typed text")


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableTypes:
    """Variable with different value types."""

    def test_variable_float(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[float] stores float values."""

        @decorator
        class TestClass(base_class):
            _ratio: Variable[float] = new(3.14)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._ratio.value).is_close_to(3.14, 0.001)

    def test_variable_no_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str] with no arg defaults to None."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.value).is_none()


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableDirectAccess:
    """Test transparent Variable access (the public API)."""

    def test_iadd(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports += operator."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count += 5
        assert_that(instance._count.value).is_equal_to(15)

    def test_isub(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports -= operator."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count -= 3
        assert_that(instance._count.value).is_equal_to(7)

    def test_imul(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports *= operator."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count *= 2
        assert_that(instance._count.value).is_equal_to(20)

    def test_itruediv(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports /= operator."""

        @decorator
        class TestClass(base_class):
            _value: Variable[float] = new(10.0)

        instance = create_and_track(qt, TestClass, base_class)
        instance._value /= 4
        assert_that(instance._value.value).is_equal_to(2.5)

    def test_ifloordiv(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports //= operator."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count //= 3
        assert_that(instance._count.value).is_equal_to(3)

    def test_imod(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable supports %= operator."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)

        instance = create_and_track(qt, TestClass, base_class)
        instance._count %= 3
        assert_that(instance._count.value).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableList:
    """Variable[list[T]] with list operations."""

    def test_list_empty_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[str]] defaults to empty list."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._items.value).is_equal_to([])

    def test_list_with_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[str]] can have initial items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b", "c"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._items.value).is_equal_to(["a", "b", "c"])

    def test_list_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Can append to list via .observable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        instance._items.observable.append("hello")  # type: ignore[union-attr]
        assert_that(instance._items.value).is_equal_to(["hello"])

    def test_list_len(self, base_class, decorator, qt: QtDriver) -> None:
        """Can get list length."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b", "c"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(len(instance._items.value)).is_equal_to(3)


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableDict:
    """Variable[dict[K,V]] with dict operations."""

    def test_dict_empty_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[str, int]] defaults to empty dict."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._data.value).is_equal_to({})

    def test_dict_with_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[str, int]] can have initial items."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"a": 1, "b": 2})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._data.value).is_equal_to({"a": 1, "b": 2})

    def test_dict_setitem(self, base_class, decorator, qt: QtDriver) -> None:
        """Can set dict items via .observable."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        instance._data.observable["key"] = 42  # type: ignore[index]
        assert_that(instance._data.value).is_equal_to({"key": 42})

    def test_dict_getitem(self, base_class, decorator, qt: QtDriver) -> None:
        """Can get dict items."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"key": 42})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._data.value["key"]).is_equal_to(42)

    def test_dict_contains(self, base_class, decorator, qt: QtDriver) -> None:
        """Can check key in dict."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"key": 42})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that("key" in instance._data.value).is_true()
        assert_that("other" in instance._data.value).is_false()


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableSet:
    """Variable[set[T]] with set operations."""

    def test_set_empty_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[set[str]] defaults to empty set."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tags.value).is_equal_to(set())

    def test_set_with_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[set[str]] can have initial items."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b", "c"})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tags.value).is_equal_to({"a", "b", "c"})

    def test_set_add(self, base_class, decorator, qt: QtDriver) -> None:
        """Can add to set via .observable."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        instance._tags.observable.add("hello")  # type: ignore[union-attr]
        assert_that(instance._tags.value).is_equal_to({"hello"})

    def test_set_add_multiple(self, base_class, decorator, qt: QtDriver) -> None:
        """Can add multiple items to set."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        instance._tags.observable.add("a")  # type: ignore[union-attr]
        instance._tags.observable.add("b")  # type: ignore[union-attr]
        instance._tags.observable.add("c")  # type: ignore[union-attr]
        assert_that(instance._tags.value).is_equal_to({"a", "b", "c"})

    def test_set_add_duplicate(self, base_class, decorator, qt: QtDriver) -> None:
        """Adding duplicate to set has no effect."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a"})

        instance = create_and_track(qt, TestClass, base_class)
        instance._tags.observable.add("a")  # type: ignore[union-attr]
        assert_that(instance._tags.value).is_equal_to({"a"})
        assert_that(len(instance._tags.value)).is_equal_to(1)

    def test_set_discard(self, base_class, decorator, qt: QtDriver) -> None:
        """Can discard from set via .observable."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b", "c"})

        instance = create_and_track(qt, TestClass, base_class)
        instance._tags.observable.discard("b")  # type: ignore[union-attr]
        assert_that(instance._tags.value).is_equal_to({"a", "c"})

    def test_set_discard_missing(self, base_class, decorator, qt: QtDriver) -> None:
        """Discarding missing item from set does not raise."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a"})

        instance = create_and_track(qt, TestClass, base_class)
        instance._tags.observable.discard("missing")  # type: ignore[union-attr]
        assert_that(instance._tags.value).is_equal_to({"a"})

    def test_set_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Can clear set via .observable."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b", "c"})

        instance = create_and_track(qt, TestClass, base_class)
        instance._tags.observable.clear()  # type: ignore[union-attr]
        assert_that(instance._tags.value).is_equal_to(set())

    def test_set_contains(self, base_class, decorator, qt: QtDriver) -> None:
        """Can check item in set."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b"})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that("a" in instance._tags.value).is_true()
        assert_that("c" in instance._tags.value).is_false()

    def test_set_len(self, base_class, decorator, qt: QtDriver) -> None:
        """Can get set length."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b", "c"})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(len(instance._tags.value)).is_equal_to(3)

    def test_set_iteration(self, base_class, decorator, qt: QtDriver) -> None:
        """Can iterate over set."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b", "c"})

        instance = create_and_track(qt, TestClass, base_class)
        items = list(instance._tags.value)
        assert_that(set(items)).is_equal_to({"a", "b", "c"})


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariablePerInstance:
    """Each instance has its own Variable values."""

    def test_instances_have_separate_values(self, base_class, decorator, qt: QtDriver) -> None:
        """Two instances have independent Variable values."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        a = create_and_track(qt, TestClass, base_class)
        b = create_and_track(qt, TestClass, base_class)

        a._count += 10
        b._count += 20

        assert_that(a._count.value).is_equal_to(10)
        assert_that(b._count.value).is_equal_to(20)

    def test_instances_have_separate_lists(self, base_class, decorator, qt: QtDriver) -> None:
        """Two instances have independent list Variables."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new()

        a = create_and_track(qt, TestClass, base_class)
        b = create_and_track(qt, TestClass, base_class)

        a._items.observable.append("a")  # type: ignore[union-attr]
        b._items.observable.append("b")  # type: ignore[union-attr]

        assert_that(a._items.value).is_equal_to(["a"])
        assert_that(b._items.value).is_equal_to(["b"])
