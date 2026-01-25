# pyright: reportPrivateUsage=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
"""Tests for Computed[T] - read-only derived variables."""

from dataclasses import dataclass, field
from enum import Enum

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


class TestComputedBasic:
    """Basic Computed[T] functionality."""

    def test_computed_from_single_variable(self, qt: QtDriver) -> None:
        """Computed value derived from a single Variable."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("hello")
            _upper: Computed[str] = new("{_name.upper()}")

        instance = qt.track(TestWidget())

        # Computed value should be derived from _name
        assert_that(instance._upper.value).is_equal_to("HELLO")

    def test_computed_updates_when_source_changes(self, qt: QtDriver) -> None:
        """Computed value updates when source Variable changes."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_count * 2}")

        instance = qt.track(TestWidget())

        assert_that(instance._doubled.value).is_equal_to(10)

        # Change source
        instance._count.value = 10

        # Computed should update
        assert_that(instance._doubled.value).is_equal_to(20)

    def test_computed_from_multiple_variables(self, qt: QtDriver) -> None:
        """Computed value derived from multiple Variables."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _first: Variable[str] = new("Hello")
            _last: Variable[str] = new("World")
            _full: Computed[str] = new("{_first} {_last}")

        instance = qt.track(TestWidget())

        assert_that(instance._full.value).is_equal_to("Hello World")

        # Change first
        instance._first.value = "Goodbye"
        assert_that(instance._full.value).is_equal_to("Goodbye World")

        # Change second
        instance._last.value = "Everyone"
        assert_that(instance._full.value).is_equal_to("Goodbye Everyone")

    def test_computed_is_read_only(self, qt: QtDriver) -> None:
        """Cannot set value on Computed."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_count * 2}")

        instance = qt.track(TestWidget())

        with pytest.raises(AttributeError):
            instance._doubled.value = 100


class TestComputedWithRecord:
    """Computed[T] with Widget[T] record types."""

    def test_computed_from_record_field(self, qt: QtDriver) -> None:
        """Computed value derived from record field."""
        from qtpie import Computed

        @dataclass
        class Person:
            first_name: str = ""
            last_name: str = ""

        @widget(record=Person("John", "Doe"))
        class TestWidget(Widget[Person]):
            _full_name: Computed[str] = new("{first_name} {last_name}")

        instance = qt.track(TestWidget())

        assert_that(instance._full_name.value).is_equal_to("John Doe")

    def test_computed_updates_when_record_field_changes(self, qt: QtDriver) -> None:
        """Computed value updates when record field changes."""
        from qtpie import Computed

        @dataclass
        class Person:
            first_name: str = ""
            last_name: str = ""

        @widget(record=Person("John", "Doe"))
        class TestWidget(Widget[Person]):
            _full_name: Computed[str] = new("{first_name} {last_name}")

        instance = qt.track(TestWidget())

        assert_that(instance._full_name.value).is_equal_to("John Doe")

        # Change record field
        instance.record.first_name = "Jane"
        assert_that(instance._full_name.value).is_equal_to("Jane Doe")

    def test_computed_with_dict_field_access(self, qt: QtDriver) -> None:
        """Computed value using dict field with bracket notation."""
        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)

        @widget(record=Response({"content-type": "application/json"}))
        class TestWidget(Widget[Response]):
            _content_type: Computed[str] = new("{headers['content-type']}")

        instance = qt.track(TestWidget())

        assert_that(instance._content_type.value).is_equal_to("application/json")

    def test_computed_with_dict_field_in_format_string(self, qt: QtDriver) -> None:
        """Computed value using dict field in format string."""
        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)

        @widget(record=Response({"content-type": "text/html"}))
        class TestWidget(Widget[Response]):
            _content_type: Computed[str] = new("Type: {headers['content-type']}")

        instance = qt.track(TestWidget())

        assert_that(instance._content_type.value).is_equal_to("Type: text/html")

    def test_computed_updates_when_record_set_later(self, qt: QtDriver) -> None:
        """Computed updates when record is set after widget creation."""
        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)

        @widget
        class TestWidget(Widget[Response]):
            _content_type: Computed[str] = new("{headers.get('content-type', 'none')}")

        instance = qt.track(TestWidget())

        # Set record
        instance.record = Response({"content-type": "application/json"})

        # Computed should update
        assert_that(instance._content_type.value).is_equal_to("application/json")

    def test_computed_with_label_updates_when_record_set_later(self, qt: QtDriver) -> None:
        """Computed bound to label updates when record is set after widget creation."""
        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)

        @widget
        class TestWidget(Widget[Response]):
            _content_type: Computed[str] = new("{headers.get('content-type', 'none')}")
            _label: QLabel = new(bind="Type: {_content_type}")

        instance = qt.track(TestWidget())

        # Set record
        instance.record = Response({"content-type": "text/html"})

        # Label should update through the computed
        assert_that(instance._label.text()).is_equal_to("Type: text/html")

    def test_computed_direct_bracket_access_with_record_set_later(self, qt: QtDriver) -> None:
        """Computed with direct bracket access updates when record is set later."""
        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)

        @widget
        class TestWidget(Widget[Response]):
            # Direct bracket access like user's code
            _content_type: Computed[str] = new("I am the {headers['content-type']}")
            _label: QLabel = new(bind="THE Content-Type: {_content_type}")

        instance = qt.track(TestWidget())

        # Set record
        instance.record = Response({"content-type": "application/json"})

        # Computed and label should update
        assert_that(instance._content_type.value).is_equal_to("I am the application/json")
        assert_that(instance._label.text()).is_equal_to("THE Content-Type: I am the application/json")


class TestComputedWithRecordPropagation:
    """Computed[T] with record propagation (e.g., tabs inheriting parent record)."""

    def test_computed_in_child_widget_with_propagated_record(self, qt: QtDriver) -> None:
        """Computed in child widget updates when parent's record is set and propagated."""
        from PySide6.QtWidgets import QTabWidget

        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)
            status_code: int = 0

        @widget(title="Body")
        class ChildWidget(Widget[Response]):
            _content_type: Computed[str] = new("Type: {headers.get('content-type', 'none')}")
            _label: QLabel = new(bind="{_content_type}")

        @widget
        class ParentWidget(Widget[Response]):
            _tabs: QTabWidget = new(tabs=[ChildWidget])

        parent = qt.track(ParentWidget())

        # Get the child widget from the tab
        child = parent._tabs.widget(0)
        assert child is not None

        # Set record on parent - should propagate to child via tabs
        parent.record = Response(headers={"content-type": "application/json"}, status_code=200)

        # Child's computed should now show the propagated record's data
        assert_that(child._label.text()).is_equal_to("Type: application/json")

    def test_computed_with_bracket_access_in_tab_child(self, qt: QtDriver) -> None:
        """Computed with bracket access in tab child works with propagated record."""
        from PySide6.QtWidgets import QTabWidget

        from qtpie import Computed

        @dataclass
        class Response:
            headers: dict[str, str] = field(default_factory=dict)

        @widget(title="Body")
        class ResponseBodyWidget(Widget[Response]):
            the_content_type: Computed[str] = new("I am the {headers['content-type']}")
            content_type_label: QLabel = new(bind="THE Content-Type: {the_content_type}")

        @widget
        class ResponseViewerWidget(Widget[Response]):
            _tabs: QTabWidget = new(tabs=[ResponseBodyWidget])

        parent = qt.track(ResponseViewerWidget())
        child = parent._tabs.widget(0)

        # Set record on parent
        parent.record = Response(headers={"content-type": "text/html"})

        # Child should have the computed value
        assert_that(child.the_content_type.value).is_equal_to("I am the text/html")
        assert_that(child.content_type_label.text()).is_equal_to("THE Content-Type: I am the text/html")


class TestComputedInBindings:
    """Computed[T] can be used in widget bindings."""

    def test_computed_used_in_label_bind(self, qt: QtDriver) -> None:
        """Computed can be referenced in widget bind= expressions."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_count * 2}")
            _label: QLabel = new(bind="Doubled: {_doubled}")

        instance = qt.track(TestWidget())

        assert_that(instance._label.text()).is_equal_to("Doubled: 10")

        # Change source, label should update through the Computed
        instance._count.value = 7
        assert_that(instance._doubled.value).is_equal_to(14)  # Computed updated
        assert_that(instance._label.text()).is_equal_to("Doubled: 14")  # Label updated reactively

    def test_label_updates_through_computed_chain(self, qt: QtDriver) -> None:
        """Changing root Variable propagates through Computed to bound widget."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _base: Variable[int] = new(10)
            _doubled: Computed[int] = new("{_base * 2}")
            _quadrupled: Computed[int] = new("{_doubled * 2}")
            _label: QLabel = new(bind="Result: {_quadrupled}")

        instance = qt.track(TestWidget())

        # Initial: 10 * 2 * 2 = 40
        assert_that(instance._label.text()).is_equal_to("Result: 40")

        # Change base to 5: 5 * 2 * 2 = 20
        instance._base.value = 5
        assert_that(instance._doubled.value).is_equal_to(10)
        assert_that(instance._quadrupled.value).is_equal_to(20)
        assert_that(instance._label.text()).is_equal_to("Result: 20")

    def test_computed_chain(self, qt: QtDriver) -> None:
        """Computed can depend on other Computed values."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _base: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_base * 2}")
            _quadrupled: Computed[int] = new("{_doubled * 2}")

        instance = qt.track(TestWidget())

        assert_that(instance._doubled.value).is_equal_to(10)
        assert_that(instance._quadrupled.value).is_equal_to(20)

        # Change base
        instance._base.value = 3
        assert_that(instance._doubled.value).is_equal_to(6)
        assert_that(instance._quadrupled.value).is_equal_to(12)


class TestComputedTypes:
    """Test Computed with various data types."""

    def test_computed_bool(self, qt: QtDriver) -> None:
        """Computed boolean from comparison."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _is_big: Computed[bool] = new("{_count > 10}")

        instance = qt.track(TestWidget())

        assert_that(instance._is_big.value).is_false()

        instance._count.value = 15
        assert_that(instance._is_big.value).is_true()

    def test_computed_float(self, qt: QtDriver) -> None:
        """Computed float from division."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _numerator: Variable[int] = new(10)
            _denominator: Variable[int] = new(4)
            _ratio: Computed[float] = new("{_numerator / _denominator}")

        instance = qt.track(TestWidget())

        assert_that(instance._ratio.value).is_equal_to(2.5)

        instance._numerator.value = 20
        assert_that(instance._ratio.value).is_equal_to(5.0)

    def test_computed_dataclass(self, qt: QtDriver) -> None:
        """Computed returns a dataclass object - uses tuple for now since local classes not in eval scope."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _key: Variable[str] = new("mykey")
            _value: Variable[int] = new(123)
            # Use tuple since local classes not accessible in eval
            _pair: Computed[tuple[str, int]] = new("{(_key, _value)}")

        instance = qt.track(TestWidget())

        assert_that(instance._pair.value[0]).is_equal_to("mykey")
        assert_that(instance._pair.value[1]).is_equal_to(123)

        # Change source - computed should return new tuple
        instance._key.value = "newkey"
        assert_that(instance._pair.value[0]).is_equal_to("newkey")

    def test_computed_nested_property_binding(self, qt: QtDriver) -> None:
        """Binding accesses nested property on Computed value."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _text: Variable[str] = new("hello world")
            # split() returns a list, we can access it
            _words: Computed[list[str]] = new("{_text.split()}")
            _first_word: Computed[str] = new("{_text.split()[0]}")
            _label: QLabel = new(bind="First word: {_first_word}")

        instance = qt.track(TestWidget())

        assert_that(instance._words.value).is_equal_to(["hello", "world"])
        assert_that(instance._first_word.value).is_equal_to("hello")
        assert_that(instance._label.text()).is_equal_to("First word: hello")

        # Change source, computed and label should update
        instance._text.value = "goodbye everyone"
        assert_that(instance._first_word.value).is_equal_to("goodbye")
        assert_that(instance._label.text()).is_equal_to("First word: goodbye")


class TestComputedExpressions:
    """Test various expression types in Computed."""

    def test_computed_with_conditionals(self, qt: QtDriver) -> None:
        """Computed with ternary conditional."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _score: Variable[int] = new(75)
            _grade: Computed[str] = new("{'Pass' if _score >= 60 else 'Fail'}")
            _label: QLabel = new(bind="Grade: {_grade}")

        instance = qt.track(TestWidget())

        assert_that(instance._grade.value).is_equal_to("Pass")
        assert_that(instance._label.text()).is_equal_to("Grade: Pass")

        instance._score.value = 50
        assert_that(instance._grade.value).is_equal_to("Fail")
        assert_that(instance._label.text()).is_equal_to("Grade: Fail")

    def test_computed_with_string_methods(self, qt: QtDriver) -> None:
        """Computed using string methods."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("  john doe  ")
            _cleaned: Computed[str] = new("{_name.strip().title()}")

        instance = qt.track(TestWidget())

        assert_that(instance._cleaned.value).is_equal_to("John Doe")

        instance._name.value = "  jane smith  "
        assert_that(instance._cleaned.value).is_equal_to("Jane Smith")

    def test_computed_with_len(self, qt: QtDriver) -> None:
        """Computed using len() builtin."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _items: Variable[str] = new("apple,banana,cherry")
            _count: Computed[int] = new("{len(_items.split(','))}")
            _label: QLabel = new(bind="Items: {_count}")

        instance = qt.track(TestWidget())

        assert_that(instance._count.value).is_equal_to(3)
        assert_that(instance._label.text()).is_equal_to("Items: 3")

        instance._items.value = "a,b,c,d,e"
        assert_that(instance._count.value).is_equal_to(5)
        assert_that(instance._label.text()).is_equal_to("Items: 5")


# Define at module level so they're in the module globals for eval


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Priority(Enum):
    LOW = 10
    MEDIUM = 50
    HIGH = 100


@dataclass
class KeyValue:
    key: str
    value: int


class TestComputedWithModuleTypes:
    """Test Computed with enums and classes defined at module level."""

    def test_computed_enum(self, qt: QtDriver) -> None:
        """Computed that returns an enum value."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _color_value: Variable[int] = new(1)
            _color: Computed[Color] = new("Color(_color_value)")

        instance = qt.track(TestWidget())

        assert_that(instance._color.value).is_equal_to(Color.RED)

        instance._color_value.value = 2
        assert_that(instance._color.value).is_equal_to(Color.GREEN)

    def test_computed_enum_name_in_binding(self, qt: QtDriver) -> None:
        """Binding accesses .name on computed enum."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _color_value: Variable[int] = new(1)
            _color: Computed[Color] = new("Color(_color_value)")
            _label: QLabel = new(bind="Color: {_color.name}")

        instance = qt.track(TestWidget())

        assert_that(instance._label.text()).is_equal_to("Color: RED")

        instance._color_value.value = 3
        assert_that(instance._label.text()).is_equal_to("Color: BLUE")

    def test_computed_enum_value_in_binding(self, qt: QtDriver) -> None:
        """Binding accesses .value on computed enum."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _priority_name: Variable[str] = new("LOW")
            _priority: Computed[Priority] = new("Priority[_priority_name]")
            _label: QLabel = new(bind="Priority: {_priority.value}")

        instance = qt.track(TestWidget())

        assert_that(instance._priority.value).is_equal_to(Priority.LOW)
        assert_that(instance._label.text()).is_equal_to("Priority: 10")

        instance._priority_name.value = "HIGH"
        assert_that(instance._priority.value).is_equal_to(Priority.HIGH)
        assert_that(instance._label.text()).is_equal_to("Priority: 100")

    def test_computed_dataclass(self, qt: QtDriver) -> None:
        """Computed that returns a dataclass instance."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _key: Variable[str] = new("mykey")
            _val: Variable[int] = new(123)
            _pair: Computed[KeyValue] = new("KeyValue(key=_key, value=_val)")

        instance = qt.track(TestWidget())

        assert_that(instance._pair.value).is_instance_of(KeyValue)
        assert_that(instance._pair.value.key).is_equal_to("mykey")
        assert_that(instance._pair.value.value).is_equal_to(123)

        instance._key.value = "newkey"
        assert_that(instance._pair.value.key).is_equal_to("newkey")

    def test_computed_dataclass_nested_binding(self, qt: QtDriver) -> None:
        """Binding accesses nested property on computed dataclass."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _key: Variable[str] = new("thekey")
            _val: Variable[int] = new(456)
            _pair: Computed[KeyValue] = new("KeyValue(key=_key, value=_val)")
            _label: QLabel = new(bind="Key={_pair.key}, Val={_pair.value}")

        instance = qt.track(TestWidget())

        assert_that(instance._label.text()).is_equal_to("Key=thekey, Val=456")

        instance._key.value = "updated"
        instance._val.value = 789
        assert_that(instance._label.text()).is_equal_to("Key=updated, Val=789")
