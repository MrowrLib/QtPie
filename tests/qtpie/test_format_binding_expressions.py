# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for complex Python expressions in format string bindings.

Tests the bind="" parameter with:
- Function calls: {len(name)}, {name.upper()}
- Math expressions: {x + y}, {(x + y) * z}
- Instance method calls: {compute_something()}
- #self placeholder: {#self}, {len(#self)}
- Format specs: {price:.2f}
"""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


class TestBuiltinFunctions:
    """Test Python builtin functions in format expressions."""

    def test_len_function(self, qt: QtDriver) -> None:
        """len() works on string variables."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("Hello")
            _label: QLabel = new(bind="{len(_name)}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("5")

    def test_len_reactivity(self, qt: QtDriver) -> None:
        """len() updates when variable changes."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("Hi")
            _label: QLabel = new(bind="{len(_name)}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("2")

        w._name.value = "Hello World"
        assert_that(w._label.text()).is_equal_to("11")

    def test_str_function(self, qt: QtDriver) -> None:
        """str() converts numbers."""

        @widget
        class Test(Widget):
            _count: Variable[int] = new(42)
            _label: QLabel = new(bind="{str(_count)}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("42")

    def test_int_function(self, qt: QtDriver) -> None:
        """int() converts strings."""

        @widget
        class Test(Widget):
            _value: Variable[str] = new("123")
            _label: QLabel = new(bind="{int(_value)}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("123")

    def test_abs_function(self, qt: QtDriver) -> None:
        """abs() works on numbers."""

        @widget
        class Test(Widget):
            _value: Variable[int] = new(-42)
            _label: QLabel = new(bind="{abs(_value)}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("42")

    def test_min_max_functions(self, qt: QtDriver) -> None:
        """min/max work on multiple variables."""

        @widget
        class Test(Widget):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)
            _min_label: QLabel = new(bind="{min(_x, _y)}")
            _max_label: QLabel = new(bind="{max(_x, _y)}")

        w = qt.track(Test())
        assert_that(w._min_label.text()).is_equal_to("10")
        assert_that(w._max_label.text()).is_equal_to("20")

    def test_round_function(self, qt: QtDriver) -> None:
        """round() works on floats."""

        @widget
        class Test(Widget):
            _value: Variable[float] = new(3.14159)
            _label: QLabel = new(bind="{round(_value, 2)}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("3.14")


class TestStringMethods:
    """Test string method calls in format expressions."""

    def test_upper_method(self, qt: QtDriver) -> None:
        """str.upper() works."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("hello")
            _label: QLabel = new(bind="{_name.upper()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("HELLO")

    def test_lower_method(self, qt: QtDriver) -> None:
        """str.lower() works."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("HELLO")
            _label: QLabel = new(bind="{_name.lower()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("hello")

    def test_title_method(self, qt: QtDriver) -> None:
        """str.title() works."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("hello world")
            _label: QLabel = new(bind="{_name.title()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("Hello World")

    def test_strip_method(self, qt: QtDriver) -> None:
        """str.strip() works."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("  hello  ")
            _label: QLabel = new(bind="{_name.strip()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("hello")

    def test_replace_method(self, qt: QtDriver) -> None:
        """str.replace() works."""

        @widget
        class Test(Widget):
            _text: Variable[str] = new("hello world")
            _label: QLabel = new(bind="{_text.replace('world', 'there')}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("hello there")

    def test_method_chain(self, qt: QtDriver) -> None:
        """Chained method calls work."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("  HELLO  ")
            _label: QLabel = new(bind="{_name.strip().lower()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("hello")

    def test_string_method_reactivity(self, qt: QtDriver) -> None:
        """String method calls update reactively."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("hello")
            _label: QLabel = new(bind="{_name.upper()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("HELLO")

        w._name.value = "world"
        assert_that(w._label.text()).is_equal_to("WORLD")


class TestMathExpressions:
    """Test math expressions in format bindings."""

    def test_addition(self, qt: QtDriver) -> None:
        """Addition works."""

        @widget
        class Test(Widget):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)
            _label: QLabel = new(bind="{_x + _y}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("30")

    def test_subtraction(self, qt: QtDriver) -> None:
        """Subtraction works."""

        @widget
        class Test(Widget):
            _x: Variable[int] = new(50)
            _y: Variable[int] = new(20)
            _label: QLabel = new(bind="{_x - _y}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("30")

    def test_multiplication(self, qt: QtDriver) -> None:
        """Multiplication works."""

        @widget
        class Test(Widget):
            _x: Variable[int] = new(5)
            _y: Variable[int] = new(6)
            _label: QLabel = new(bind="{_x * _y}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("30")

    def test_division(self, qt: QtDriver) -> None:
        """Division works."""

        @widget
        class Test(Widget):
            _x: Variable[float] = new(10.0)
            _y: Variable[float] = new(4.0)
            _label: QLabel = new(bind="{_x / _y}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("2.5")

    def test_complex_expression(self, qt: QtDriver) -> None:
        """Complex math expression with parentheses works."""

        @widget
        class Test(Widget):
            _x: Variable[int] = new(2)
            _y: Variable[int] = new(3)
            _z: Variable[int] = new(4)
            _label: QLabel = new(bind="{(_x + _y) * _z}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("20")  # (2 + 3) * 4

    def test_math_reactivity(self, qt: QtDriver) -> None:
        """Math expressions update when any variable changes."""

        @widget
        class Test(Widget):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(5)
            _label: QLabel = new(bind="{_x + _y}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("15")

        w._x.value = 20
        assert_that(w._label.text()).is_equal_to("25")

        w._y.value = 10
        assert_that(w._label.text()).is_equal_to("30")


class TestFormatSpecs:
    """Test Python format specifications."""

    def test_float_precision(self, qt: QtDriver) -> None:
        """Float formatting with precision works."""

        @widget
        class Test(Widget):
            _price: Variable[float] = new(19.99)
            _label: QLabel = new(bind="${_price:.2f}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("$19.99")

    def test_percentage(self, qt: QtDriver) -> None:
        """Percentage formatting works."""

        @widget
        class Test(Widget):
            _rate: Variable[float] = new(0.157)
            _label: QLabel = new(bind="{_rate:.1%}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("15.7%")

    def test_padding(self, qt: QtDriver) -> None:
        """Padding/width formatting works."""

        @widget
        class Test(Widget):
            _num: Variable[int] = new(42)
            _label: QLabel = new(bind="{_num:05d}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("00042")

    def test_format_spec_with_expression(self, qt: QtDriver) -> None:
        """Format spec works on computed expression."""

        @widget
        class Test(Widget):
            _price: Variable[float] = new(10.0)
            _tax_rate: Variable[float] = new(0.1)
            _label: QLabel = new(bind="${_price * (1 + _tax_rate):.2f}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("$11.00")


class TestSelfPlaceholder:
    """Test #self placeholder for accessing widget instance."""

    def test_self_in_expression(self, qt: QtDriver) -> None:
        """#self refers to the widget."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("Test Widget")
            _label: QLabel = new(bind="{#self.objectName()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("Test")  # Class name is default

    def test_self_property_access(self, qt: QtDriver) -> None:
        """#self.property accesses widget attribute."""

        @widget
        class Test(Widget):
            title: str = "My Title"
            _label: QLabel = new(bind="{#self.title}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("My Title")


class TestInstanceMethods:
    """Test calling instance methods from format expressions."""

    def test_simple_method_call(self, qt: QtDriver) -> None:
        """Method call without parens works (auto-invoked if callable)."""

        @widget
        class Test(Widget):
            _label: QLabel = new(bind="{get_greeting()}")

            def get_greeting(self) -> str:
                return "Hello!"

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("Hello!")

    def test_method_with_variable(self, qt: QtDriver) -> None:
        """Method that uses a variable works."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("World")
            _label: QLabel = new(bind="{greet(_name)}")

            def greet(self, name: str) -> str:
                return f"Hello, {name}!"

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("Hello, World!")


class TestCombinedExpressions:
    """Test combinations of different expression types."""

    def test_function_in_format_string(self, qt: QtDriver) -> None:
        """Functions in multi-field format strings work."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("alice")
            _label: QLabel = new(bind="Hello, {_name.title()}!")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("Hello, Alice!")

    def test_multiple_expressions(self, qt: QtDriver) -> None:
        """Multiple expressions in one format string work."""

        @widget
        class Test(Widget):
            _first: Variable[str] = new("hello")
            _second: Variable[str] = new("world")
            _label: QLabel = new(bind="{_first.upper()} {_second.upper()}")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("HELLO WORLD")

    def test_math_and_string_combined(self, qt: QtDriver) -> None:
        """Math and string operations combined work."""

        @widget
        class Test(Widget):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            _label: QLabel = new(bind="{len(_items)} items")

        w = qt.track(Test())
        assert_that(w._label.text()).is_equal_to("3 items")


class TestErrorHandling:
    """Test graceful error handling in expressions."""

    def test_invalid_expression_shows_empty(self, qt: QtDriver) -> None:
        """Invalid expression shows empty string (allows using `or 'default'` pattern)."""

        @widget
        class Test(Widget):
            _label: QLabel = new(bind="{undefined_variable}")

        w = qt.track(Test())
        # Should show empty string rather than crash (allows `or 'default'` pattern)
        assert_that(w._label.text()).is_equal_to("")

    def test_exception_in_expression_shows_empty(self, qt: QtDriver) -> None:
        """Exception in expression shows empty string (allows using `or 'default'` pattern)."""

        @widget
        class Test(Widget):
            _value: Variable[int] = new(0)
            _label: QLabel = new(bind="{1 / _value}")

        w = qt.track(Test())
        # Division by zero should be caught, show empty string
        assert_that(w._label.text()).is_equal_to("")

    def test_none_with_fallback(self, qt: QtDriver) -> None:
        """None values can use 'or' fallback pattern."""

        @widget
        class Test(Widget):
            _value: Variable[str | None] = new(None)
            _label: QLabel = new(bind="{_value or 'N/A'}")

        w = qt.track(Test())
        # Should fall back to 'N/A' since _value is None
        assert_that(w._label.text()).is_equal_to("N/A")

        # When value is set, should show the value
        w._value.value = "Hello"
        assert_that(w._label.text()).is_equal_to("Hello")


class TestObjectPropertyBinding:
    """Test binding to dataclass/object properties with expressions."""

    def test_nested_property_in_expression(self, qt: QtDriver) -> None:
        """Nested property access in expressions works."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @widget
        class Test(Widget[Person]):
            _label: QLabel = new(bind="{name.upper()}")

        w = qt.track(Test())
        w._qtpie.record_state.observable.name.set("alice")  # type: ignore[union-attr]
        assert_that(w._label.text()).is_equal_to("ALICE")

    def test_expression_with_record_field(self, qt: QtDriver) -> None:
        """Math expressions with record fields work."""

        @dataclass
        class Counter:
            count: int = 0

        @widget
        class Test(Widget[Counter]):
            _label: QLabel = new(bind="{count * 2}")

        w = qt.track(Test())
        w._qtpie.record_state.observable.count.set(21)  # type: ignore[union-attr]
        assert_that(w._label.text()).is_equal_to("42")


class TestVariableWidgetBindExpressions:
    """Test bind= with Variable[T, QWidget] pattern and special placeholders."""

    def test_variable_widget_self_refers_to_value(self, qt: QtDriver) -> None:
        """#self in Variable[T, QLabel] context refers to Variable's value."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLabel] = new("Hello")(bind="Value is: {#self}!")

        w = qt.track(Test())
        assert_that(w._name.widget.text()).is_equal_to("Value is: Hello!")

    def test_variable_widget_self_with_method(self, qt: QtDriver) -> None:
        """#self.method() works on Variable's value."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLabel] = new("hello")(bind="Upper: {#self.upper()}")

        w = qt.track(Test())
        assert_that(w._name.widget.text()).is_equal_to("Upper: HELLO")

    def test_variable_widget_self_with_len(self, qt: QtDriver) -> None:
        """len(#self) works on Variable's value."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLabel] = new("Hello")(bind="Length: {len(#self)}")

        w = qt.track(Test())
        assert_that(w._name.widget.text()).is_equal_to("Length: 5")

    def test_variable_widget_var_placeholder(self, qt: QtDriver) -> None:
        """#var is alias for Variable's value."""

        @widget
        class Test(Widget):
            _count: Variable[int, QLabel] = new(42)(bind="Count is: {#var}")

        w = qt.track(Test())
        assert_that(w._count.widget.text()).is_equal_to("Count is: 42")

    def test_variable_widget_var_with_math(self, qt: QtDriver) -> None:
        """Math on #var works."""

        @widget
        class Test(Widget):
            _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

        w = qt.track(Test())
        assert_that(w._count.widget.text()).is_equal_to("Double: 20")

    def test_variable_widget_widget_placeholder(self, qt: QtDriver) -> None:
        """#widget refers to parent widget instance."""

        @widget
        class Test(Widget):
            title: str = "MyWidget"
            _label: Variable[str, QLabel] = new("x")(bind="Widget title: {#widget.title}")

        w = qt.track(Test())
        assert_that(w._label.widget.text()).is_equal_to("Widget title: MyWidget")

    def test_variable_widget_self_reactivity(self, qt: QtDriver) -> None:
        """#self updates when Variable changes."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}")

        w = qt.track(Test())
        assert_that(w._name.widget.text()).is_equal_to("Value: Hello")

        w._name.value = "World"
        assert_that(w._name.widget.text()).is_equal_to("Value: World")

    def test_variable_widget_combined_placeholders(self, qt: QtDriver) -> None:
        """Can use #self, #var, and #widget together."""

        @widget
        class Test(Widget):
            title: str = "Test"
            _val: Variable[int, QLabel] = new(5)(bind="{#widget.title}: {#self} doubled is {#var * 2}")

        w = qt.track(Test())
        assert_that(w._val.widget.text()).is_equal_to("Test: 5 doubled is 10")
