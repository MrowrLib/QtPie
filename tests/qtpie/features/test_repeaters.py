# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportCallIssue=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportArgumentType=false
# pyright: reportIndexIssue=false
# pyright: reportUnknownLambdaType=false
# pyright: reportOptionalMemberAccess=false
"""Tests for widget repeaters across Widget, Window, and App.

Tests list, dict, and set repeaters (widget generation from collections).
Menu is excluded as it uses QAction repeaters, not QWidget repeaters.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import DictWidgetRepeater, SetWidgetRepeater, Variable, WidgetRepeater, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for object binding."""

    name: str
    age: int = 0


# =============================================================================
# List Repeater Basic
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterBasic:
    """Basic list repeater functionality."""

    def test_creates_widgets_for_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[T], W] creates widgets for initial items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

    def test_empty_list_no_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty list creates no widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(0)

    def test_widgets_are_correct_type(self, base_class, decorator, qt: QtDriver) -> None:
        """Repeater creates widgets of specified type."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int], QSpinBox] = new([1, 2])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[int] = instance._items.widget
        assert_that(repeater.widget_at(0)).is_instance_of(QSpinBox)
        assert_that(repeater.widget_at(1)).is_instance_of(QSpinBox)

    def test_primitives_show_values(self, base_class, decorator, qt: QtDriver) -> None:
        """Primitive values display in widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int], QLabel] = new([10, 20, 30])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[int] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("10")
        assert_that(repeater.widget_at(1).text()).is_equal_to("20")
        assert_that(repeater.widget_at(2).text()).is_equal_to("30")


# =============================================================================
# List Repeater Granular Sync
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterSync:
    """List repeater granular sync operations."""

    def test_append_creates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list adds widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

        instance._items.observable.append("c")
        assert_that(repeater.widget_count()).is_equal_to(3)

    def test_insert_creates_widget_at_index(self, base_class, decorator, qt: QtDriver) -> None:
        """Inserting at index adds widget at position."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        instance._items.observable.insert(1, "b")
        assert_that(repeater.widget_count()).is_equal_to(3)
        assert_that(repeater.widget_at(1).text()).is_equal_to("b")

    def test_remove_destroys_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list removes widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

        instance._items.observable.remove("b")
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_clear_destroys_all(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list removes all widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

        instance._items.observable.clear()
        assert_that(repeater.widget_count()).is_equal_to(0)

    def test_replace_updates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Replacing item updates widget value."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["old"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("old")

        instance._items.observable[0] = "new"
        assert_that(repeater.widget_at(0).text()).is_equal_to("new")


# =============================================================================
# List Repeater Format Expressions
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterFormat:
    """List repeater format expressions."""

    def test_format_self(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self} shows item value."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int], QLabel] = new([10, 20])(bind="{#self}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[int] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("10")
        assert_that(repeater.widget_at(1).text()).is_equal_to("20")

    def test_format_index(self, base_class, decorator, qt: QtDriver) -> None:
        """{#index} shows item index."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])(bind="{#index}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("0")
        assert_that(repeater.widget_at(1).text()).is_equal_to("1")
        assert_that(repeater.widget_at(2).text()).is_equal_to("2")

    def test_format_index_and_self(self, base_class, decorator, qt: QtDriver) -> None:
        """Combined {#index} and {#self}."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b"])(bind="[{#index}] {#self}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("[0] a")
        assert_that(repeater.widget_at(1).text()).is_equal_to("[1] b")

    def test_format_object_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Object property binding {name}."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3), Dog("Rex", 5)])(bind="{name}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[Dog] = instance._dogs.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("Fido")
        assert_that(repeater.widget_at(1).text()).is_equal_to("Rex")

    def test_format_multiple_properties(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple object properties in format."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3)])(bind="{name} is {age}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[Dog] = instance._dogs.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("Fido is 3")


# =============================================================================
# List Repeater Two-Way Binding
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterTwoWay:
    """List repeater two-way binding."""

    def test_edit_widget_updates_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Editing widget updates list item."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLineEdit] = new(["hello"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        edit = repeater.widget_at(0)
        edit.setText("world")
        assert_that(instance._items.observable[0]).is_equal_to("world")

    def test_list_change_updates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing list updates widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["hello"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        instance._items.observable[0] = "world"
        assert_that(repeater.widget_at(0).text()).is_equal_to("world")


# =============================================================================
# Dict Repeater Basic
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDictRepeaterBasic:
    """Basic dict repeater functionality."""

    def test_creates_widgets_for_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[K, V], W] creates widgets for items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"a": 1, "b": 2})
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels).is_instance_of(DictWidgetRepeater)
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_empty_dict_no_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty dict creates no widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({})
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(0)

    def test_setitem_creates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting new key creates widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"a": 1})
            _labels: list[QLabel] = new(bind="_items", format="{#key}={#value}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(1)

        instance._items["b"] = 2
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_delitem_destroys_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Deleting key removes widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"a": 1, "b": 2})
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(2)

        del instance._items.observable["a"]
        assert_that(instance._labels.widget_count()).is_equal_to(1)


# =============================================================================
# Dict Repeater Format Expressions
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDictRepeaterFormat:
    """Dict repeater format expressions."""

    def test_format_key_value(self, base_class, decorator, qt: QtDriver) -> None:
        """{#key} and {#value} placeholders."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"Alice": 100})
            _labels: list[QLabel] = new(bind="_items", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)
        label = instance._labels.widget_for_key("Alice")
        assert_that(label).is_not_none()
        assert_that(label.text()).is_equal_to("Alice: 100")

    def test_format_value_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Object value properties in format."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[dict[str, Dog]] = new({"fido": Dog("Fido", 3)})
            _labels: list[QLabel] = new(bind="_dogs", format="{#key}: {name} is {age}")

        instance = create_and_track(qt, TestClass, base_class)
        label = instance._labels.widget_for_key("fido")
        assert_that(label.text()).is_equal_to("fido: Fido is 3")


# =============================================================================
# Set Repeater Basic (Variable[set[T], W] syntax)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSetRepeaterBasic:
    """Basic set repeater functionality using Variable[set[T], W] syntax."""

    def test_creates_widgets_for_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[set[T], W] creates widgets for items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"a", "b", "c"})  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

    def test_empty_set_no_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty set creates no widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new(set())  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(0)

    def test_add_creates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Adding to set creates widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"a"})  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(1)

        instance._items.observable.add("b")
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_discard_destroys_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Discarding from set removes widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"a", "b"})  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

        instance._items.observable.discard("a")
        assert_that(repeater.widget_count()).is_equal_to(1)


# =============================================================================
# Set Repeater Format
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSetRepeaterFormat:
    """Set repeater format expressions."""

    def test_format_self(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self} shows item value via bind=."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"hello"})(bind="{#self}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        # Set order is not guaranteed, so just check count
        assert_that(repeater.widget_count()).is_equal_to(1)


# =============================================================================
# list[QWidget] = new(bind=...) Syntax
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListWidgetBindSyntax:
    """list[QWidget] = new(bind=...) syntax."""

    def test_list_qlabel_bound_to_list_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] = new(bind='_items') creates repeater."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a", "b"])
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels).is_instance_of(WidgetRepeater)
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_list_qlabel_with_format_string(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] with format= template."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _labels: list[QLabel] = new(bind="_dogs", format="{name}: {age}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_at(0).text()).is_equal_to("Fido: 3")

    def test_list_qlabel_syncs_with_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] syncs when bound variable changes."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a"])
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(1)

        instance._items.append("b")
        assert_that(instance._labels.widget_count()).is_equal_to(2)


# =============================================================================
# Widget Kwargs Applied to Repeater Items
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestRepeaterWidgetKwargs:
    """Widget kwargs applied to each repeater item."""

    def test_kwargs_applied_to_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget kwargs applied to initial items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLineEdit] = new(["a", "b"])(maxLength=5)  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        assert_that(repeater.widget_at(0).maxLength()).is_equal_to(5)
        assert_that(repeater.widget_at(1).maxLength()).is_equal_to(5)

    def test_kwargs_applied_to_new_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget kwargs applied to dynamically added items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLineEdit] = new([])(maxLength=10)  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        instance._items.append("new")
        assert_that(repeater.widget_at(0).maxLength()).is_equal_to(10)
