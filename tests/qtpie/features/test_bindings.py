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


# =============================================================================
# Widget[T | None] Record Binding - bind="name" vs bind="{name}"
# =============================================================================


class TestRecordNoneBinding:
    """Test that bind= works correctly when Widget[T | None] has record=None initially.

    This reproduces the issue where:
    - bind="{name}" (format string) works - subscribes to proxy, re-evaluates when target changes
    - bind="name" (simple string) fails - resolve_binding_source skips when target is None
    """

    def test_bind_format_string_works_when_record_none_then_set(self, qt: QtDriver) -> None:
        """bind='{name}' correctly updates when record changes from None to a value.

        This is the WORKING case - format binding subscribes to the proxy and
        re-evaluates when the target changes.
        """
        from qtpie import State, Var, Widget, state, widget

        @state
        class PersonState(State):
            name: Var[str] = new("Alice")

        @widget
        class ChildWidget(Widget[PersonState | None]):
            label: QLabel = new(bind="{name}")

        @widget
        class OuterWidget(Widget):
            person_state: Var[PersonState | None] = new(None)
            child: ChildWidget = new(bind="person_state")

        instance = OuterWidget()
        qt.track(instance)
        instance.show()

        # Initially record is None, label should be empty
        assert_that(instance.child.label.text()).is_equal_to("")

        # Set a record - with bind="{name}", this WILL update the label
        instance.person_state = PersonState()

        # This works!
        assert_that(instance.child.label.text()).is_equal_to("Alice")

    def test_bind_simple_string_when_record_none_then_set(self, qt: QtDriver) -> None:
        """bind='name' updates when record changes from None to a value.

        This tests deferred binding - when record is initially None, the binding
        should be set up later when the record becomes available.
        """
        from qtpie import State, Var, Widget, state, widget

        @state
        class PersonState(State):
            name: Var[str] = new("Bob")

        @widget
        class ChildWidget(Widget[PersonState | None]):
            label: QLabel = new(bind="name")

        @widget
        class OuterWidget(Widget):
            person_state: Var[PersonState | None] = new(None)
            child: ChildWidget = new(bind="person_state")

        instance = OuterWidget()
        qt.track(instance)
        instance.show()

        # Initially record is None, label should be empty
        assert_that(instance.child.label.text()).is_equal_to("")

        # Set a record - binding should now connect and update the label
        instance.person_state = PersonState()

        # Label should now show the record's name
        assert_that(instance.child.label.text()).is_equal_to("Bob")

        # Reactivity should work - changing the record field updates the label
        instance.person_state.value.name = "Changed"  # type: ignore[union-attr]
        assert_that(instance.child.label.text()).is_equal_to("Changed")

    def test_bind_simple_string_works_when_record_set_in_decorator(self, qt: QtDriver) -> None:
        """bind='name' works when record is provided in decorator (not None initially).

        This confirms bind="name" works fine when record is available at init time.
        """
        from qtpie import State, Var, Widget, state, widget

        @state
        class PersonState(State):
            name: Var[str] = new("Charlie")

        @widget(record=PersonState())
        class DirectWidget(Widget[PersonState]):
            label: QLabel = new(bind="name")

        instance = DirectWidget()
        qt.track(instance)
        instance.show()

        # Record was set in decorator, so binding works immediately
        assert_that(instance.label.text()).is_equal_to("Charlie")

        # And reactivity works too
        instance.record.name = "Dave"
        assert_that(instance.label.text()).is_equal_to("Dave")

    def test_bind_simple_string_two_way_when_record_none_then_set(self, qt: QtDriver) -> None:
        """bind='name' supports two-way binding when record changes from None to a value.

        Two-way binding means:
        1. Record field changes -> widget updates
        2. Widget changes -> record field updates
        """
        from qtpie import State, Var, Widget, state, widget

        @state
        class PersonState(State):
            name: Var[str] = new("Initial")

        @widget
        class ChildWidget(Widget[PersonState | None]):
            name_input: QLineEdit = new(bind="name")

        @widget
        class OuterWidget(Widget):
            person_state: Var[PersonState | None] = new(None)
            child: ChildWidget = new(bind="person_state")

        instance = OuterWidget()
        qt.track(instance)
        instance.show()

        # Initially record is None, input should be empty
        assert_that(instance.child.name_input.text()).is_equal_to("")

        # Set a record - binding should now connect
        instance.person_state = PersonState()

        # Input should show the record's name
        assert_that(instance.child.name_input.text()).is_equal_to("Initial")

        # Two-way binding: record -> widget
        instance.person_state.value.name = "FromRecord"  # type: ignore[union-attr]
        assert_that(instance.child.name_input.text()).is_equal_to("FromRecord")

        # Two-way binding: widget -> record
        instance.child.name_input.setText("FromWidget")
        assert_that(instance.person_state.value.name()).is_equal_to("FromWidget")  # type: ignore[union-attr]


# =============================================================================
# Enum Field Attribute Access in Bindings (Regression Test)
# =============================================================================


class TestEnumFieldAttributeBinding:
    """Test that binding to enum field attributes like {body_type.name} works reactively.

    This is a regression test for a bug where:
    - bind="{body_type}" worked (subscribed to the Observable for body_type)
    - bind="{body_type.name}" did NOT update (only subscribed to proxy, not the field Observable)

    The fix ensures that for nested paths like "body_type.name" where the root is a record
    field, we also subscribe to the Observable for the root field (body_type), not just
    the proxy.
    """

    def test_enum_field_name_attribute_updates_reactively(self, qt: QtDriver) -> None:
        """bind='{field.name}' updates when enum field changes.

        Reproduces the exact issue from forc2/request_editor.py where:
        - body_type_label: QLabel = new(bind="Body Type: {body_type}") worked
        - body_type_name_label: QLabel = new(bind="Body Type: {body_type.name}") did NOT update
        """
        from dataclasses import dataclass
        from enum import Enum

        from qtpie import Widget, widget

        class BodyType(Enum):
            NONE = "none"
            JSON = "json"
            XML = "xml"
            TEXT = "text"

        @dataclass
        class Request:
            body_type: BodyType = BodyType.NONE

        @widget(record=Request())
        class RequestBodyWidget(Widget[Request]):
            # This worked before the fix
            body_type_label: QLabel = new(bind="Body Type: {body_type}")
            # This did NOT update before the fix
            body_type_name_label: QLabel = new(bind="Body Type: {body_type.name}")

        instance = RequestBodyWidget()
        qt.track(instance)
        instance.show()

        # Initial state - both labels should show NONE
        assert_that(instance.body_type_label.text()).is_equal_to("Body Type: BodyType.NONE")
        assert_that(instance.body_type_name_label.text()).is_equal_to("Body Type: NONE")

        # Change the enum value
        instance.record.body_type = BodyType.JSON

        # Both should update - this is the regression test!
        assert_that(instance.body_type_label.text()).is_equal_to("Body Type: BodyType.JSON")
        assert_that(instance.body_type_name_label.text()).is_equal_to("Body Type: JSON")

        # Change again to verify continued reactivity
        instance.record.body_type = BodyType.XML
        assert_that(instance.body_type_label.text()).is_equal_to("Body Type: BodyType.XML")
        assert_that(instance.body_type_name_label.text()).is_equal_to("Body Type: XML")

    def test_enum_field_value_attribute_updates_reactively(self, qt: QtDriver) -> None:
        """bind='{field.value}' updates when enum field changes."""
        from dataclasses import dataclass
        from enum import Enum

        from qtpie import Widget, widget

        class Status(Enum):
            PENDING = "pending"
            ACTIVE = "active"
            COMPLETED = "completed"

        @dataclass
        class Task:
            status: Status = Status.PENDING

        @widget(record=Task())
        class TaskWidget(Widget[Task]):
            status_value_label: QLabel = new(bind="Status: {status.value}")

        instance = TaskWidget()
        qt.track(instance)
        instance.show()

        assert_that(instance.status_value_label.text()).is_equal_to("Status: pending")

        instance.record.status = Status.ACTIVE
        assert_that(instance.status_value_label.text()).is_equal_to("Status: active")

        instance.record.status = Status.COMPLETED
        assert_that(instance.status_value_label.text()).is_equal_to("Status: completed")

    def test_multiple_enum_attribute_bindings(self, qt: QtDriver) -> None:
        """Multiple labels binding to different enum attributes all update."""
        from dataclasses import dataclass
        from enum import Enum

        from qtpie import Widget, widget

        class Priority(Enum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3

        @dataclass
        class Item:
            priority: Priority = Priority.LOW

        @widget(record=Item())
        class ItemWidget(Widget[Item]):
            raw_label: QLabel = new(bind="{priority}")
            name_label: QLabel = new(bind="{priority.name}")
            value_label: QLabel = new(bind="{priority.value}")

        instance = ItemWidget()
        qt.track(instance)
        instance.show()

        # Initial state
        assert_that(instance.raw_label.text()).is_equal_to("Priority.LOW")
        assert_that(instance.name_label.text()).is_equal_to("LOW")
        assert_that(instance.value_label.text()).is_equal_to("1")

        # Change the enum
        instance.record.priority = Priority.HIGH

        # All three should update
        assert_that(instance.raw_label.text()).is_equal_to("Priority.HIGH")
        assert_that(instance.name_label.text()).is_equal_to("HIGH")
        assert_that(instance.value_label.text()).is_equal_to("3")

    def test_visible_binding_with_enum_name_attribute(self, qt: QtDriver) -> None:
        """visible='{field.name in [...]}' updates when enum field changes.

        This is the exact bug from forc2/request_editor.py where visible= bindings
        using enum .name attribute didn't update reactively.
        """
        from dataclasses import dataclass
        from enum import Enum

        from qtpie import Widget, widget

        class BodyType(Enum):
            NONE = "none"
            JSON = "json"
            TEXT = "text"
            FORM = "form"

        @dataclass
        class Request:
            body_type: BodyType = BodyType.NONE

        @widget(record=Request())
        class RequestBodyWidget(Widget[Request]):
            # This label is visible only for JSON/TEXT body types
            text_editor: QLabel = new("Text Editor", visible="{body_type.name in ['JSON', 'TEXT']}")
            # This label is visible only for FORM body type
            form_editor: QLabel = new("Form Editor", visible="{body_type.name == 'FORM'}")

        instance = RequestBodyWidget()
        qt.track(instance)
        instance.show()

        # Initial state - NONE, both should be hidden
        assert_that(instance.text_editor.isVisible()).is_false()
        assert_that(instance.form_editor.isVisible()).is_false()

        # Change to JSON - text_editor should become visible
        instance.record.body_type = BodyType.JSON
        assert_that(instance.text_editor.isVisible()).is_true()
        assert_that(instance.form_editor.isVisible()).is_false()

        # Change to FORM - form_editor should become visible, text_editor hidden
        instance.record.body_type = BodyType.FORM
        assert_that(instance.text_editor.isVisible()).is_false()
        assert_that(instance.form_editor.isVisible()).is_true()

        # Change to TEXT - text_editor should become visible again
        instance.record.body_type = BodyType.TEXT
        assert_that(instance.text_editor.isVisible()).is_true()
        assert_that(instance.form_editor.isVisible()).is_false()

        # Change back to NONE - both hidden again
        instance.record.body_type = BodyType.NONE
        assert_that(instance.text_editor.isVisible()).is_false()
        assert_that(instance.form_editor.isVisible()).is_false()

    def test_enabled_binding_with_enum_value_attribute(self, qt: QtDriver) -> None:
        """enabled='{field.value == ...}' updates when enum field changes."""
        from dataclasses import dataclass
        from enum import Enum

        from PySide6.QtWidgets import QPushButton

        from qtpie import Widget, widget

        class Status(Enum):
            DRAFT = "draft"
            READY = "ready"
            SENT = "sent"

        @dataclass
        class Message:
            status: Status = Status.DRAFT

        @widget(record=Message())
        class MessageWidget(Widget[Message]):
            send_btn: QPushButton = new("Send", enabled="{status.value == 'ready'}")

        instance = MessageWidget()
        qt.track(instance)
        instance.show()

        # Initial state - DRAFT, button disabled
        assert_that(instance.send_btn.isEnabled()).is_false()

        # Change to READY - button enabled
        instance.record.status = Status.READY
        assert_that(instance.send_btn.isEnabled()).is_true()

        # Change to SENT - button disabled again
        instance.record.status = Status.SENT
        assert_that(instance.send_btn.isEnabled()).is_false()


# =============================================================================
# Binding Resolution Order - Record fields before underscore fallback
# =============================================================================


class TestBindingResolutionOrder:
    """Test that binding resolution checks record fields BEFORE underscore fallback.

    This is a regression test for a bug where:
    - _body_text: QPlainTextEdit = new(bind="{body_text}") would find ITSELF
    - Because the code tried _body_text (underscore prefix) before checking the record

    The correct order is:
    1. Exact name on widget fields
    2. Record fields (annotations and @property)
    3. THEN underscore fallback
    """

    def test_bind_resolves_to_record_not_self(self, qt: QtDriver) -> None:
        """bind='{body_text}' on _body_text field resolves to record.body_text, not the field itself.

        This is the exact bug from forc2 where:
        - _body_text: QPlainTextEdit = new(bind="{body_text}")
        - Should bind to Response.body_text, NOT find _body_text widget
        """
        from dataclasses import dataclass

        from PySide6.QtWidgets import QPlainTextEdit

        from qtpie import Widget, widget

        @dataclass
        class Response:
            body_text: str = "Response body content"

        @widget(record=Response())
        class ResponseBodyWidget(Widget[Response]):
            # Field is named _body_text, bind references body_text (no underscore)
            # Should resolve to record.body_text, NOT to self._body_text
            _body_text: QPlainTextEdit = new(bind="{body_text}", readOnly=True)

        instance = ResponseBodyWidget()
        qt.track(instance)
        instance.show()

        # The QPlainTextEdit should show the RECORD's body_text value
        assert_that(instance._body_text.toPlainText()).is_equal_to("Response body content")

        # Changing the record should update the widget
        instance.record.body_text = "Updated content"
        assert_that(instance._body_text.toPlainText()).is_equal_to("Updated content")

    def test_bind_underscore_variable_to_record_field(self, qt: QtDriver) -> None:
        """bind='name' (no underscore) on _name field resolves to record.name."""
        from dataclasses import dataclass

        from qtpie import Widget, widget

        @dataclass
        class Person:
            name: str = "Alice"

        @widget(record=Person())
        class PersonWidget(Widget[Person]):
            # Field is _name, bind='name' should resolve to record.name
            _name: QLabel = new(bind="name")

        instance = PersonWidget()
        qt.track(instance)
        instance.show()

        assert_that(instance._name.text()).is_equal_to("Alice")

        instance.record.name = "Bob"
        assert_that(instance._name.text()).is_equal_to("Bob")

    def test_explicit_underscore_resolves_to_widget_field(self, qt: QtDriver) -> None:
        """bind='_count' (with underscore) resolves to widget._count Variable."""
        from qtpie import Widget, widget

        @widget
        class CounterWidget(Widget):
            _count: Variable[int] = new(42)
            _label: QLabel = new(bind="_count")

        instance = CounterWidget()
        qt.track(instance)
        instance.show()

        # Explicit underscore should resolve to the widget's _count Variable
        assert_that(instance._label.text()).is_equal_to("42")

        instance._count.value = 100
        assert_that(instance._label.text()).is_equal_to("100")


# =============================================================================
# @property Support in Record Bindings
# =============================================================================


class TestPropertyBindingSupport:
    """Test that @property methods on record types are accessible via bindings.

    Before the fix, only annotated fields (in __annotations__) were checked.
    @property methods were not found, causing underscore fallback to incorrectly match.
    """

    def test_bind_to_property_on_record(self, qt: QtDriver) -> None:
        """bind='{full_name}' resolves to record's @property full_name."""
        from dataclasses import dataclass

        from qtpie import Widget, widget

        @dataclass
        class Person:
            first_name: str = "John"
            last_name: str = "Doe"

            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        @widget(record=Person())
        class PersonWidget(Widget[Person]):
            _full_name: QLabel = new(bind="{full_name}")

        instance = PersonWidget()
        qt.track(instance)
        instance.show()

        # Should resolve to the @property, not try to find _full_name on widget
        assert_that(instance._full_name.text()).is_equal_to("John Doe")

    def test_bind_to_property_with_underscore_field_name(self, qt: QtDriver) -> None:
        """bind='{body_text}' on _body_text field resolves to record's @property body_text."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QPlainTextEdit

        from qtpie import Widget, widget

        @dataclass
        class Response:
            raw_body: str = "raw content"

            @property
            def body_text(self) -> str:
                return f"Formatted: {self.raw_body}"

        @widget(record=Response())
        class ResponseWidget(Widget[Response]):
            # _body_text field with bind="{body_text}"
            # body_text is a @property, not an annotation
            _body_text: QPlainTextEdit = new(bind="{body_text}", readOnly=True)

        instance = ResponseWidget()
        qt.track(instance)
        instance.show()

        # Should resolve to record's @property body_text
        assert_that(instance._body_text.toPlainText()).is_equal_to("Formatted: raw content")

    def test_property_initial_value_resolved(self, qt: QtDriver) -> None:
        """@property is correctly resolved at widget creation time.

        Note: @property values don't automatically update when dependent fields change.
        For reactive computed values, use Computed[T] instead.
        """
        from dataclasses import dataclass

        from qtpie import Widget, widget

        @dataclass
        class Rectangle:
            width: int = 10
            height: int = 5

            @property
            def area(self) -> int:
                return self.width * self.height

        @widget(record=Rectangle())
        class RectangleWidget(Widget[Rectangle]):
            _area: QLabel = new(bind="Area: {area}")

        instance = RectangleWidget()
        qt.track(instance)
        instance.show()

        # @property should be resolved correctly at widget creation
        assert_that(instance._area.text()).is_equal_to("Area: 50")
