# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for bind= parameter across Widget, Window, Menu, and App.

Tests simple bindings, format expressions, auto-binding, and two-way binding.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QCheckBox, QLabel, QLineEdit

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# Simple bind= to Variable
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSimpleBinding:
    """Basic bind= to Variable works across widget class types."""

    def test_bind_to_variable_int(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='_count' displays int Variable value."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(42)
            _label: QLabel = new(bind="_count")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("42")

    def test_bind_to_variable_str(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='_name' displays str Variable value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Hello")
            _label: QLabel = new(bind="_name")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Hello")

    def test_bind_to_variable_float(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='_value' displays float Variable value."""

        @decorator
        class TestClass(base_class):
            _value: Variable[float] = new(3.14)
            _label: QLabel = new(bind="_value")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("3.14")

    def test_bind_to_variable_bool(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='_flag' displays bool Variable value."""

        @decorator
        class TestClass(base_class):
            _flag: Variable[bool] = new(True)
            _label: QLabel = new(bind="_flag")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("True")

    def test_bind_updates_on_change(self, base_class, decorator, qt: QtDriver) -> None:
        """Value change updates bound widget."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            _label: QLabel = new(bind="_count")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("0")

        instance._count.value = 100
        assert_that(instance._label.text()).is_equal_to("100")

    def test_bind_updates_multiple_times(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple value changes all update bound widget."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("first")
            _label: QLabel = new(bind="_name")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("first")

        instance._name.value = "second"
        assert_that(instance._label.text()).is_equal_to("second")

        instance._name.value = "third"
        assert_that(instance._label.text()).is_equal_to("third")


# =============================================================================
# Format Expression Bindings
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFormatExpressionBinding:
    """Format expression bindings like bind='{_name}' work across class types."""

    def test_simple_format(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_name}' displays Variable value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Hello")
            _label: QLabel = new(bind="{_name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Hello")

    def test_format_with_prefix(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='Name: {_name}' adds static text."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("World")
            _label: QLabel = new(bind="Name: {_name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Name: World")

    def test_format_with_suffix(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_count} items' adds static text suffix."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(5)
            _label: QLabel = new(bind="{_count} items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("5 items")

    def test_format_multiple_variables(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_first} {_last}' combines multiple Variables."""

        @decorator
        class TestClass(base_class):
            _first: Variable[str] = new("Hello")
            _last: Variable[str] = new("World")
            _label: QLabel = new(bind="{_first} {_last}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Hello World")

    def test_format_with_method(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_name.upper()}' calls string method."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("hello")
            _label: QLabel = new(bind="{_name.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("HELLO")

    def test_format_with_len(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{len(_name)}' calls builtin function."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Hello")
            _label: QLabel = new(bind="{len(_name)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("5")

    def test_format_with_math(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_x + _y}' evaluates math expression."""

        @decorator
        class TestClass(base_class):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)
            _label: QLabel = new(bind="{_x + _y}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("30")

    def test_format_with_complex_math(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{(_x + _y) * _z}' handles parentheses."""

        @decorator
        class TestClass(base_class):
            _x: Variable[int] = new(2)
            _y: Variable[int] = new(3)
            _z: Variable[int] = new(4)
            _label: QLabel = new(bind="{(_x + _y) * _z}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("20")  # (2 + 3) * 4

    def test_format_with_spec(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='${_price:.2f}' uses format spec."""

        @decorator
        class TestClass(base_class):
            _price: Variable[float] = new(19.99)
            _label: QLabel = new(bind="${_price:.2f}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("$19.99")

    def test_format_with_percentage(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_rate:.1%}' formats as percentage."""

        @decorator
        class TestClass(base_class):
            _rate: Variable[float] = new(0.157)
            _label: QLabel = new(bind="{_rate:.1%}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("15.7%")

    def test_format_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """Format expression updates when any variable changes."""

        @decorator
        class TestClass(base_class):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(5)
            _label: QLabel = new(bind="{_x + _y}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("15")

        instance._x.value = 20
        assert_that(instance._label.text()).is_equal_to("25")

        instance._y.value = 10
        assert_that(instance._label.text()).is_equal_to("30")


# =============================================================================
# Two-Way Binding (QLineEdit, QCheckBox)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTwoWayBinding:
    """Two-way binding between Variable and editable widgets."""

    def test_lineedit_displays_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """QLineEdit shows initial Variable value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("Initial")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.text()).is_equal_to("Initial")

    def test_lineedit_updates_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Typing in QLineEdit updates Variable."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.widget.setText("typed text")
        assert_that(instance._name.value).is_equal_to("typed text")

    def test_variable_updates_lineedit(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting Variable.value updates QLineEdit."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("initial")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "programmatic"
        assert_that(instance._name.widget.text()).is_equal_to("programmatic")

    def test_checkbox_displays_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """QCheckBox shows initial Variable value."""

        @decorator
        class TestClass(base_class):
            _enabled: Variable[bool, QCheckBox] = new(True)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._enabled.widget.isChecked()).is_true()

    def test_checkbox_updates_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Clicking QCheckBox updates Variable."""

        @decorator
        class TestClass(base_class):
            _enabled: Variable[bool, QCheckBox] = new(False)

        instance = create_and_track(qt, TestClass, base_class)
        instance._enabled.widget.setChecked(True)
        assert_that(instance._enabled.value).is_true()

    def test_variable_updates_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting Variable.value updates QCheckBox."""

        @decorator
        class TestClass(base_class):
            _enabled: Variable[bool, QCheckBox] = new(False)

        instance = create_and_track(qt, TestClass, base_class)
        instance._enabled.value = True
        assert_that(instance._enabled.widget.isChecked()).is_true()

    def test_bidirectional_sync(self, base_class, decorator, qt: QtDriver) -> None:
        """Both directions of two-way binding work."""

        @decorator
        class TestClass(base_class):
            _text: Variable[str, QLineEdit] = new("start")

        instance = create_and_track(qt, TestClass, base_class)

        # Widget -> Variable
        instance._text.widget.setText("from widget")
        assert_that(instance._text.value).is_equal_to("from widget")

        # Variable -> Widget
        instance._text.value = "from code"
        assert_that(instance._text.widget.text()).is_equal_to("from code")


# =============================================================================
# Variable[T, W] with bind= (format expression on inline widget)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVariableWidgetBind:
    """Variable[T, QLabel] with bind= for formatted display."""

    def test_self_placeholder(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self} refers to Variable's value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.text()).is_equal_to("Value: Hello")

    def test_self_with_method(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self.upper()} calls method on value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLabel] = new("hello")(bind="Upper: {#self.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.text()).is_equal_to("Upper: HELLO")

    def test_self_with_len(self, base_class, decorator, qt: QtDriver) -> None:
        """{len(#self)} calls builtin on value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLabel] = new("Hello")(bind="Length: {len(#self)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.text()).is_equal_to("Length: 5")

    def test_var_placeholder(self, base_class, decorator, qt: QtDriver) -> None:
        """{#var} is alias for Variable's value."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int, QLabel] = new(42)(bind="Count: {#var}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.widget.text()).is_equal_to("Count: 42")

    def test_var_with_math(self, base_class, decorator, qt: QtDriver) -> None:
        """{#var * 2} does math on value."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.widget.text()).is_equal_to("Double: 20")

    def test_self_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self} updates when Variable changes."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.text()).is_equal_to("Value: Hello")

        instance._name.value = "World"
        assert_that(instance._name.widget.text()).is_equal_to("Value: World")


# =============================================================================
# Binding with List Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestBindingWithList:
    """Binding expressions work with list Variables."""

    def test_bind_list_length(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{len(_items)}' shows list length."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b", "c"])
            _label: QLabel = new(bind="{len(_items)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("3")

    def test_bind_list_join(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{', '.join(_items)}' joins list."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b", "c"])
            _label: QLabel = new(bind="{', '.join(_items)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("a, b, c")

    def test_bind_list_first_item(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_items[0]}' shows first item."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["first", "second"])
            _label: QLabel = new(bind="{_items[0]}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("first")

    def test_bind_list_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """List binding updates when list changes."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a"])
            _label: QLabel = new(bind="{len(_items)} items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("1 items")

        instance._items.observable.append("b")  # type: ignore[union-attr]
        assert_that(instance._label.text()).is_equal_to("2 items")


# =============================================================================
# Binding with Dict Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestBindingWithDict:
    """Binding expressions work with dict Variables."""

    def test_bind_dict_length(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{len(_data)}' shows dict length."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"a": 1, "b": 2})
            _label: QLabel = new(bind="{len(_data)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("2")

    def test_bind_dict_value(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_data['key']}' shows dict value."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"score": 100})
            _label: QLabel = new(bind="{_data['score']}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("100")

    def test_bind_dict_keys(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{list(_data.keys())}' shows dict keys."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"a": 1, "b": 2})
            _label: QLabel = new(bind="{sorted(_data.keys())}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("['a', 'b']")

    def test_bind_dict_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """Dict binding updates when dict changes."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new()
            _label: QLabel = new(bind="{len(_data)} entries")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("0 entries")

        instance._data.observable["key"] = 42  # type: ignore[index]
        assert_that(instance._label.text()).is_equal_to("1 entries")


# =============================================================================
# Binding with Set Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestBindingWithSet:
    """Binding expressions work with set Variables."""

    def test_bind_set_length(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{len(_tags)}' shows set length."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b", "c"})
            _label: QLabel = new(bind="{len(_tags)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("3")

    def test_bind_set_contains(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{'x' in _tags}' checks membership."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b"})
            _label: QLabel = new(bind="{'a' in _tags}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("True")

    def test_bind_set_sorted(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{sorted(_tags)}' shows sorted set."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"c", "a", "b"})
            _label: QLabel = new(bind="{sorted(_tags)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("['a', 'b', 'c']")

    def test_bind_set_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """Set binding updates when set changes."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new()
            _label: QLabel = new(bind="{len(_tags)} tags")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("0 tags")

        instance._tags.observable.add("new")  # type: ignore[union-attr]
        assert_that(instance._label.text()).is_equal_to("1 tags")


# =============================================================================
# Conditional Expressions in Bindings
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestConditionalBinding:
    """Conditional expressions in bindings."""

    def test_ternary_true(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{'Yes' if _flag else 'No'}' shows Yes when True."""

        @decorator
        class TestClass(base_class):
            _flag: Variable[bool] = new(True)
            _label: QLabel = new(bind="{'Yes' if _flag else 'No'}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Yes")

    def test_ternary_false(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{'Yes' if _flag else 'No'}' shows No when False."""

        @decorator
        class TestClass(base_class):
            _flag: Variable[bool] = new(False)
            _label: QLabel = new(bind="{'Yes' if _flag else 'No'}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("No")

    def test_ternary_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """Conditional updates when Variable changes."""

        @decorator
        class TestClass(base_class):
            _flag: Variable[bool] = new(True)
            _label: QLabel = new(bind="{'Active' if _flag else 'Inactive'}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Active")

        instance._flag.value = False
        assert_that(instance._label.text()).is_equal_to("Inactive")

    def test_comparison_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{_count > 0}' evaluates comparison."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(5)
            _label: QLabel = new(bind="{_count > 0}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("True")

    def test_complex_conditional(self, base_class, decorator, qt: QtDriver) -> None:
        """Complex conditional with multiple variables."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            _label: QLabel = new(bind="{_count if _count > 0 else 'none'}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("none")

        instance._count.value = 5
        assert_that(instance._label.text()).is_equal_to("5")


# =============================================================================
# Multiple Bindings on Same Widget
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMultipleBindings:
    """Multiple widgets bound to same Variable."""

    def test_multiple_labels_same_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple labels can bind to same Variable."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Hello")
            _label1: QLabel = new(bind="_name")
            _label2: QLabel = new(bind="_name")
            _label3: QLabel = new(bind="Name: {_name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label1.text()).is_equal_to("Hello")
        assert_that(instance._label2.text()).is_equal_to("Hello")
        assert_that(instance._label3.text()).is_equal_to("Name: Hello")

    def test_multiple_labels_update_together(self, base_class, decorator, qt: QtDriver) -> None:
        """All bound labels update when Variable changes."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("First")
            _label1: QLabel = new(bind="_name")
            _label2: QLabel = new(bind="Value: {_name}")

        instance = create_and_track(qt, TestClass, base_class)

        instance._name.value = "Second"
        assert_that(instance._label1.text()).is_equal_to("Second")
        assert_that(instance._label2.text()).is_equal_to("Value: Second")


# =============================================================================
# Instance Methods in Bindings
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMethodBinding:
    """Calling instance methods from binding expressions."""

    def test_simple_method_call(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{get_greeting()}' calls instance method."""

        @decorator
        class TestClass(base_class):
            _label: QLabel = new(bind="{get_greeting()}")

            def get_greeting(self) -> str:
                return "Hello!"

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Hello!")

    def test_method_with_variable_arg(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{greet(_name)}' passes Variable to method."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("World")
            _label: QLabel = new(bind="{greet(_name)}")

            def greet(self, name: str) -> str:
                return f"Hello, {name}!"

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Hello, World!")

    def test_method_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """Method binding updates when Variable argument changes."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(5)
            _label: QLabel = new(bind="{format_count(_count)}")

            def format_count(self, n: int) -> str:
                return f"{n} item{'s' if n != 1 else ''}"

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("5 items")

        instance._count.value = 1
        assert_that(instance._label.text()).is_equal_to("1 item")


# =============================================================================
# Signal Handler Order Tests - User handlers should see UPDATED values
# =============================================================================


class TestSignalHandlerOrderSimpleWidgets:
    """Test that user signal handlers see UPDATED values after widget changes.

    This tests the same bug pattern fixed for QComboBox/QListView/QTableView/QTreeView,
    but for simple widgets like QLineEdit, QSpinBox, QCheckBox, and QSlider.
    """

    def test_lineedit_textchanged_sees_updated_value(self, qt: QtDriver) -> None:
        """QLineEdit textChanged handler sees updated Variable value."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QTabWidget

        from qtpie import Widget, widget

        @dataclass
        class Config:
            name: str = "initial"

        @dataclass
        class Settings:
            config: Config | None = None

        call_count = {"value": 0}
        seen_values: list[str] = []

        @widget(title="Config Tab")
        class ConfigTab(Widget[Settings]):
            _name: QLineEdit = new(
                bind="config?.name",
                textChanged="_on_text_changed",
            )

            def _on_text_changed(self) -> None:
                call_count["value"] += 1
                if self.record_value and self.record_value.config:
                    seen_values.append(self.record_value.config.name)

        @widget
        class ChildWidget(Widget[Settings]):
            _tabs: QTabWidget = new(tabs=[ConfigTab])

        @widget(record=Settings(config=Config(name="initial")))
        class ParentWidget(Widget[Settings]):
            _child: ChildWidget

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        call_count["value"] = 0
        seen_values.clear()

        config_tab_widget = instance._child._tabs.widget(0)
        assert isinstance(config_tab_widget, ConfigTab)
        config_tab = config_tab_widget

        # Simulate user typing
        config_tab._name.setText("updated")

        assert_that(call_count["value"]).is_equal_to(1)
        assert_that(seen_values).is_equal_to(["updated"])

    def test_spinbox_valuechanged_sees_updated_value(self, qt: QtDriver) -> None:
        """QSpinBox valueChanged handler sees updated Variable value."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QSpinBox, QTabWidget

        from qtpie import Widget, widget

        @dataclass
        class Config:
            count: int = 0

        @dataclass
        class Settings:
            config: Config | None = None

        call_count = {"value": 0}
        seen_values: list[int] = []

        @widget(title="Config Tab")
        class ConfigTab(Widget[Settings]):
            _count: QSpinBox = new(
                bind="config?.count",
                valueChanged="_on_value_changed",
            )

            def _on_value_changed(self) -> None:
                call_count["value"] += 1
                if self.record_value and self.record_value.config:
                    seen_values.append(self.record_value.config.count)

        @widget
        class ChildWidget(Widget[Settings]):
            _tabs: QTabWidget = new(tabs=[ConfigTab])

        @widget(record=Settings(config=Config(count=0)))
        class ParentWidget(Widget[Settings]):
            _child: ChildWidget

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        call_count["value"] = 0
        seen_values.clear()

        config_tab_widget = instance._child._tabs.widget(0)
        assert isinstance(config_tab_widget, ConfigTab)
        config_tab = config_tab_widget

        # Simulate user changing value
        config_tab._count.setValue(42)

        assert_that(call_count["value"]).is_equal_to(1)
        assert_that(seen_values).is_equal_to([42])

    def test_checkbox_toggled_sees_updated_value(self, qt: QtDriver) -> None:
        """QCheckBox toggled handler sees updated Variable value."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QTabWidget

        from qtpie import Widget, widget

        @dataclass
        class Config:
            enabled: bool = False

        @dataclass
        class Settings:
            config: Config | None = None

        call_count = {"value": 0}
        seen_values: list[bool] = []

        @widget(title="Config Tab")
        class ConfigTab(Widget[Settings]):
            _enabled: QCheckBox = new(
                "Enable feature",
                bind="config?.enabled",
                toggled="_on_toggled",
            )

            def _on_toggled(self) -> None:
                call_count["value"] += 1
                if self.record_value and self.record_value.config:
                    seen_values.append(self.record_value.config.enabled)

        @widget
        class ChildWidget(Widget[Settings]):
            _tabs: QTabWidget = new(tabs=[ConfigTab])

        @widget(record=Settings(config=Config(enabled=False)))
        class ParentWidget(Widget[Settings]):
            _child: ChildWidget

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        call_count["value"] = 0
        seen_values.clear()

        config_tab_widget = instance._child._tabs.widget(0)
        assert isinstance(config_tab_widget, ConfigTab)
        config_tab = config_tab_widget

        # Simulate user clicking checkbox
        config_tab._enabled.setChecked(True)

        assert_that(call_count["value"]).is_equal_to(1)
        assert_that(seen_values).is_equal_to([True])

    def test_slider_valuechanged_sees_updated_value(self, qt: QtDriver) -> None:
        """QSlider valueChanged handler sees updated Variable value."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QSlider, QTabWidget

        from qtpie import Widget, widget

        @dataclass
        class Config:
            volume: int = 50

        @dataclass
        class Settings:
            config: Config | None = None

        call_count = {"value": 0}
        seen_values: list[int] = []

        @widget(title="Config Tab")
        class ConfigTab(Widget[Settings]):
            _volume: QSlider = new(
                bind="config?.volume",
                valueChanged="_on_value_changed",
            )

            def _on_value_changed(self) -> None:
                call_count["value"] += 1
                if self.record_value and self.record_value.config:
                    seen_values.append(self.record_value.config.volume)

        @widget
        class ChildWidget(Widget[Settings]):
            _tabs: QTabWidget = new(tabs=[ConfigTab])

        @widget(record=Settings(config=Config(volume=50)))
        class ParentWidget(Widget[Settings]):
            _child: ChildWidget

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        call_count["value"] = 0
        seen_values.clear()

        config_tab_widget = instance._child._tabs.widget(0)
        assert isinstance(config_tab_widget, ConfigTab)
        config_tab = config_tab_widget

        # Simulate user moving slider
        config_tab._volume.setValue(75)

        assert_that(call_count["value"]).is_equal_to(1)
        assert_that(seen_values).is_equal_to([75])
