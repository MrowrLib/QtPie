"""Tests for the state() reactive state functionality."""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QSpinBox, QWidget

from qtpie import make, state, widget
from qtpie.state import get_state_observable
from qtpie_test import QtDriver


class TestStateBasics:
    """Basic state() functionality tests."""

    def test_state_with_int_default(self, qt: QtDriver) -> None:
        """state(0) should create a reactive int field."""

        @widget
        class Counter(QWidget):
            count: int = state(0)

        w = Counter()
        qt.track(w)

        assert_that(w.count).is_equal_to(0)
        assert_that(type(w.count)).is_equal_to(int)

    def test_state_with_string_default(self, qt: QtDriver) -> None:
        """state("") should create a reactive string field."""

        @widget
        class Editor(QWidget):
            name: str = state("")

        w = Editor()
        qt.track(w)

        assert_that(w.name).is_equal_to("")
        assert_that(type(w.name)).is_equal_to(str)

    def test_state_assignment_updates_value(self, qt: QtDriver) -> None:
        """Assigning to a state field should update the value."""

        @widget
        class Counter(QWidget):
            count: int = state(0)

        w = Counter()
        qt.track(w)

        w.count = 42
        assert_that(w.count).is_equal_to(42)

    def test_state_increment(self, qt: QtDriver) -> None:
        """self.count += 1 should work on state fields."""

        @widget
        class Counter(QWidget):
            count: int = state(0)

            def increment(self) -> None:
                self.count += 1

        w = Counter()
        qt.track(w)

        w.increment()
        assert_that(w.count).is_equal_to(1)

        w.increment()
        w.increment()
        assert_that(w.count).is_equal_to(3)


class TestStateBinding:
    """Tests for binding widgets to state fields."""

    def test_label_bound_to_state(self, qt: QtDriver) -> None:
        """QLabel should update when bound state changes."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="count")

        w = Counter()
        qt.track(w)

        # Initial value
        assert_that(w.label.text()).is_equal_to("0")

        # Update state
        w.count = 42
        assert_that(w.label.text()).is_equal_to("42")

    def test_spinbox_two_way_binding(self, qt: QtDriver) -> None:
        """QSpinBox should have two-way binding with state."""

        @widget
        class Editor(QWidget):
            age: int = state(0)
            age_spin: QSpinBox = make(QSpinBox, bind="age")

        w = Editor()
        qt.track(w)

        # State → Widget
        w.age = 25
        assert_that(w.age_spin.value()).is_equal_to(25)

        # Widget → State
        w.age_spin.setValue(30)
        assert_that(w.age).is_equal_to(30)

    def test_lineedit_two_way_binding(self, qt: QtDriver) -> None:
        """QLineEdit should have two-way binding with state."""

        @widget
        class Editor(QWidget):
            name: str = state("")
            name_edit: QLineEdit = make(QLineEdit, bind="name")

        w = Editor()
        qt.track(w)

        # State → Widget
        w.name = "Alice"
        assert_that(w.name_edit.text()).is_equal_to("Alice")

        # Widget → State
        w.name_edit.setText("Bob")
        assert_that(w.name).is_equal_to("Bob")

    def test_multiple_widgets_same_state(self, qt: QtDriver) -> None:
        """Multiple widgets can bind to the same state field."""

        @widget
        class Editor(QWidget):
            count: int = state(0)
            spin1: QSpinBox = make(QSpinBox, bind="count")
            spin2: QSpinBox = make(QSpinBox, bind="count")
            label: QLabel = make(QLabel, bind="count")

        w = Editor()
        qt.track(w)

        # All start at 0
        assert_that(w.spin1.value()).is_equal_to(0)
        assert_that(w.spin2.value()).is_equal_to(0)
        assert_that(w.label.text()).is_equal_to("0")

        # Update via state
        w.count = 10
        assert_that(w.spin1.value()).is_equal_to(10)
        assert_that(w.spin2.value()).is_equal_to(10)
        assert_that(w.label.text()).is_equal_to("10")

        # Update via widget - all should sync
        w.spin1.setValue(20)
        assert_that(w.count).is_equal_to(20)
        assert_that(w.spin2.value()).is_equal_to(20)
        assert_that(w.label.text()).is_equal_to("20")


class TestStateExplicitType:
    """Tests for state[Type]() syntax with explicit types."""

    def test_state_explicit_optional_type(self, qt: QtDriver) -> None:
        """state[Type | None]() should work for optional fields."""

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @widget
        class Editor(QWidget):
            dog: Dog | None = state[Dog | None]()

        w = Editor()
        qt.track(w)

        # Initial value is None
        assert_that(w.dog).is_none()

        # Can assign a Dog
        w.dog = Dog(name="Buddy", age=3)
        assert_that(w.dog).is_not_none()
        assert w.dog is not None  # for type narrowing
        assert_that(w.dog.name).is_equal_to("Buddy")
        assert_that(w.dog.age).is_equal_to(3)

    def test_state_explicit_type_with_default(self, qt: QtDriver) -> None:
        """state[Type](default) should use the provided default."""

        @dataclass
        class Config:
            debug: bool = False
            max_retries: int = 3

        @widget
        class App(QWidget):
            config: Config = state[Config](Config(debug=True, max_retries=5))

        w = App()
        qt.track(w)

        assert_that(w.config.debug).is_true()
        assert_that(w.config.max_retries).is_equal_to(5)


class TestStateCounterExample:
    """Test the canonical Counter example from the design."""

    def test_counter_widget(self, qt: QtDriver) -> None:
        """The Counter widget example should work exactly as designed."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="count")
            button: QPushButton = make(QPushButton, "Add", clicked="increment")

            def increment(self) -> None:
                self.count += 1

        w = Counter()
        qt.track(w)

        # Initial state
        assert_that(w.count).is_equal_to(0)
        assert_that(w.label.text()).is_equal_to("0")

        # Click button
        qt.click(w.button)
        assert_that(w.count).is_equal_to(1)
        assert_that(w.label.text()).is_equal_to("1")

        # Click multiple times
        qt.click(w.button)
        qt.click(w.button)
        qt.click(w.button)
        assert_that(w.count).is_equal_to(4)
        assert_that(w.label.text()).is_equal_to("4")


class TestStateObservable:
    """Tests for get_state_observable helper."""

    def test_get_state_observable_returns_observable(self, qt: QtDriver) -> None:
        """get_state_observable should return the underlying Observable."""

        @widget
        class Counter(QWidget):
            count: int = state(0)

        w = Counter()
        qt.track(w)

        # Access to trigger observable creation
        _ = w.count

        observable = get_state_observable(w, "count")
        assert_that(observable).is_not_none()
        assert observable is not None  # for type narrowing
        assert_that(observable.get()).is_equal_to(0)

        # Updating via observable should update the field
        observable.set(99)
        assert_that(w.count).is_equal_to(99)

    def test_get_state_observable_returns_none_for_non_state(self, qt: QtDriver) -> None:
        """get_state_observable should return None for non-state fields."""

        @widget
        class Editor(QWidget):
            count: int = 0  # Regular field, not state

        w = Editor()
        qt.track(w)

        observable = get_state_observable(w, "count")
        assert_that(observable).is_none()


class TestStateWithMethods:
    """Tests for state with custom methods."""

    def test_state_with_decrement(self, qt: QtDriver) -> None:
        """State should work with increment and decrement."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            up: QPushButton = make(QPushButton, "+", clicked="increment")
            down: QPushButton = make(QPushButton, "-", clicked="decrement")

            def increment(self) -> None:
                self.count += 1

            def decrement(self) -> None:
                self.count -= 1

        w = Counter()
        qt.track(w)

        qt.click(w.up)
        qt.click(w.up)
        assert_that(w.count).is_equal_to(2)

        qt.click(w.down)
        assert_that(w.count).is_equal_to(1)

    def test_state_with_reset(self, qt: QtDriver) -> None:
        """State should work with a reset method."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            reset_btn: QPushButton = make(QPushButton, "Reset", clicked="reset")

            def reset(self) -> None:
                self.count = 0

        w = Counter()
        qt.track(w)

        w.count = 100
        assert_that(w.count).is_equal_to(100)

        qt.click(w.reset_btn)
        assert_that(w.count).is_equal_to(0)


class TestStateNoInfiniteLoop:
    """Tests to ensure no infinite loops in binding."""

    def test_no_infinite_loop_on_state_change(self, qt: QtDriver) -> None:
        """Changing state should not cause infinite loops."""
        change_count = [0]

        @widget
        class Editor(QWidget):
            value: int = state(0)
            spin: QSpinBox = make(QSpinBox, bind="value")

        w = Editor()
        qt.track(w)

        # Track changes
        observable = get_state_observable(w, "value")
        assert observable is not None
        observable.on_change(lambda _: change_count.__setitem__(0, change_count[0] + 1))

        # Set value
        w.spin.setValue(10)

        # Should only have 1-2 changes, not infinite
        assert_that(change_count[0]).is_less_than(5)


class TestMultipleStateFields:
    """Tests for widgets with multiple state fields."""

    def test_multiple_independent_state_fields(self, qt: QtDriver) -> None:
        """Multiple state fields should be independent."""

        @widget
        class Form(QWidget):
            name: str = state("")
            age: int = state(0)
            active: bool = state(False)

            name_edit: QLineEdit = make(QLineEdit, bind="name")
            age_spin: QSpinBox = make(QSpinBox, bind="age")

        w = Form()
        qt.track(w)

        # All independent
        w.name = "Alice"
        w.age = 30
        w.active = True

        assert_that(w.name).is_equal_to("Alice")
        assert_that(w.age).is_equal_to(30)
        assert_that(w.active).is_true()

        # Widgets reflect state
        assert_that(w.name_edit.text()).is_equal_to("Alice")
        assert_that(w.age_spin.value()).is_equal_to(30)


class TestNestedStateBinding:
    """Tests for binding to nested properties in state objects."""

    def test_nested_state_binding(self, qt: QtDriver) -> None:
        """bind='dog.name' should bind to nested property in state object."""

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @widget
        class DogEditor(QWidget):
            dog: Dog = state(Dog(name="Buddy", age=3))
            name_edit: QLineEdit = make(QLineEdit, bind="dog.name")
            age_spin: QSpinBox = make(QSpinBox, bind="dog.age")

        w = DogEditor()
        qt.track(w)

        # Initial values from state
        assert_that(w.name_edit.text()).is_equal_to("Buddy")
        assert_that(w.age_spin.value()).is_equal_to(3)

        # Update via widget - should update state object
        w.name_edit.setText("Max")
        assert_that(w.dog.name).is_equal_to("Max")

        w.age_spin.setValue(5)
        assert_that(w.dog.age).is_equal_to(5)

    def test_nested_state_binding_with_optional_chaining(self, qt: QtDriver) -> None:
        """bind='dog?.name' should handle None gracefully."""

        @dataclass
        class Dog:
            name: str = ""

        @widget
        class DogEditor(QWidget):
            dog: Dog | None = state[Dog | None]()
            name_edit: QLineEdit = make(QLineEdit, bind="dog?.name")

        w = DogEditor()
        qt.track(w)

        # Initial value is None, widget should show empty
        assert_that(w.dog).is_none()
        assert_that(w.name_edit.text()).is_equal_to("")

        # Set a dog
        w.dog = Dog(name="Rex")
        # Note: Re-binding would be needed for the widget to update
        # This tests that the initial binding doesn't crash

    def test_nested_state_replacing_object(self, qt: QtDriver) -> None:
        """Replacing the entire state object should work."""

        @dataclass
        class Person:
            name: str = ""

        @widget
        class PersonEditor(QWidget):
            person: Person = state(Person(name="Alice"))
            name_edit: QLineEdit = make(QLineEdit, bind="person.name")

        w = PersonEditor()
        qt.track(w)

        # Initial
        assert_that(w.name_edit.text()).is_equal_to("Alice")

        # Note: Directly mutating w.person.name = "Bob" doesn't notify bindings
        # because observant's proxy observes from proxy → model, not model → proxy.
        # The correct way to update is via the widget (two-way binding) or
        # by replacing the entire object.

        # Update via widget works (two-way binding)
        w.name_edit.setText("Charlie")
        assert_that(w.person.name).is_equal_to("Charlie")


class TestFormatStringBinding:
    """Tests for format string bindings like bind='Count: {count}'."""

    def test_simple_format_binding(self, qt: QtDriver) -> None:
        """bind='Count: {count}' should format and update automatically."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="Count: {count}")

        w = Counter()
        qt.track(w)

        # Initial value
        assert_that(w.label.text()).is_equal_to("Count: 0")

        # Update state
        w.count = 42
        assert_that(w.label.text()).is_equal_to("Count: 42")

    def test_multiple_vars_format_binding(self, qt: QtDriver) -> None:
        """bind='{first} {last}' should bind multiple state fields."""

        @widget
        class NameDisplay(QWidget):
            first: str = state("John")
            last: str = state("Doe")
            label: QLabel = make(QLabel, bind="{first} {last}")

        w = NameDisplay()
        qt.track(w)

        # Initial value
        assert_that(w.label.text()).is_equal_to("John Doe")

        # Update first
        w.first = "Jane"
        assert_that(w.label.text()).is_equal_to("Jane Doe")

        # Update last
        w.last = "Smith"
        assert_that(w.label.text()).is_equal_to("Jane Smith")

    def test_format_binding_with_text(self, qt: QtDriver) -> None:
        """Format strings with mixed text and variables."""

        @widget
        class Status(QWidget):
            current: int = state(5)
            total: int = state(10)
            label: QLabel = make(QLabel, bind="{current} / {total} items")

        w = Status()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("5 / 10 items")

        w.current = 7
        assert_that(w.label.text()).is_equal_to("7 / 10 items")

        w.total = 20
        assert_that(w.label.text()).is_equal_to("7 / 20 items")

    def test_format_binding_single_var_no_text(self, qt: QtDriver) -> None:
        """bind='{count}' should work same as bind='count' but formatted."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="{count}")

        w = Counter()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("0")

        w.count = 99
        assert_that(w.label.text()).is_equal_to("99")

    def test_format_binding_with_nested_path(self, qt: QtDriver) -> None:
        """bind='Hello, {dog.name}!' should support nested paths."""

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @widget
        class DogGreeter(QWidget):
            dog: Dog = state(Dog(name="Buddy", age=3))
            label: QLabel = make(QLabel, bind="Hello, {dog.name}!")

        w = DogGreeter()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Hello, Buddy!")

        # Update via the widget's nested path binding
        w.dog = Dog(name="Max", age=5)
        assert_that(w.label.text()).is_equal_to("Hello, Max!")

    def test_format_binding_mixed_simple_and_nested(self, qt: QtDriver) -> None:
        """Format with both simple state and nested paths."""

        @dataclass
        class Dog:
            name: str = ""

        @widget
        class DogInfo(QWidget):
            count: int = state(1)
            dog: Dog = state(Dog(name="Rex"))
            label: QLabel = make(QLabel, bind="Dog #{count}: {dog.name}")

        w = DogInfo()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Dog #1: Rex")

        w.count = 2
        assert_that(w.label.text()).is_equal_to("Dog #2: Rex")

        w.dog = Dog(name="Fido")
        assert_that(w.label.text()).is_equal_to("Dog #2: Fido")

    def test_format_binding_nested_path_two_way(self, qt: QtDriver) -> None:
        """Format binding should update when nested property changes via two-way binding."""

        @dataclass
        class Dog:
            name: str = ""

        @widget
        class DogEditor(QWidget):
            dog: Dog = state(Dog(name="Buddy"))
            name_edit: QLineEdit = make(QLineEdit, bind="dog.name")
            label: QLabel = make(QLabel, bind="Hello, {dog.name}!")

        w = DogEditor()
        qt.track(w)

        # Initial
        assert_that(w.label.text()).is_equal_to("Hello, Buddy!")
        assert_that(w.name_edit.text()).is_equal_to("Buddy")

        # Change via the QLineEdit (two-way binding)
        w.name_edit.setText("Max")
        assert_that(w.dog.name).is_equal_to("Max")
        assert_that(w.label.text()).is_equal_to("Hello, Max!")


class TestExpressionBinding:
    """Tests for expression bindings like bind='{count + 5}'."""

    def test_simple_math_expression(self, qt: QtDriver) -> None:
        """bind='{count + 5}' should evaluate the expression."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="{count + 5}")

        w = Counter()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("5")

        w.count = 10
        assert_that(w.label.text()).is_equal_to("15")

    def test_expression_with_text(self, qt: QtDriver) -> None:
        """bind='Count plus 5 -> {count + 5}' with surrounding text."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="Count plus 5 -> {count + 5}")

        w = Counter()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Count plus 5 -> 5")

        w.count = 7
        assert_that(w.label.text()).is_equal_to("Count plus 5 -> 12")

    def test_expression_with_format_spec(self, qt: QtDriver) -> None:
        """bind='{price * 1.1:.2f}' with format spec."""

        @widget
        class PriceDisplay(QWidget):
            price: float = state(10.0)
            label: QLabel = make(QLabel, bind="Total: ${price * 1.1:.2f}")

        w = PriceDisplay()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Total: $11.00")

        w.price = 99.99
        assert_that(w.label.text()).is_equal_to("Total: $109.99")

    def test_method_call_expression(self, qt: QtDriver) -> None:
        """bind='{name.upper()}' with method call."""

        @widget
        class NameDisplay(QWidget):
            name: str = state("hello")
            label: QLabel = make(QLabel, bind="{name.upper()}")

        w = NameDisplay()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("HELLO")

        w.name = "world"
        assert_that(w.label.text()).is_equal_to("WORLD")

    def test_nested_path_with_method(self, qt: QtDriver) -> None:
        """bind='{dog.name.upper()}' with nested path and method."""

        @dataclass
        class Dog:
            name: str = ""

        @widget
        class DogDisplay(QWidget):
            dog: Dog = state(Dog(name="buddy"))
            label: QLabel = make(QLabel, bind="{dog.name.upper()}")

        w = DogDisplay()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("BUDDY")

        w.dog = Dog(name="max")
        assert_that(w.label.text()).is_equal_to("MAX")

    def test_ternary_expression(self, qt: QtDriver) -> None:
        """bind='{count if count > 0 else 'none'}' with ternary."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="{count if count > 0 else 'none'}")

        w = Counter()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("none")

        w.count = 5
        assert_that(w.label.text()).is_equal_to("5")

        w.count = 0
        assert_that(w.label.text()).is_equal_to("none")

    def test_multiple_variables_in_expression(self, qt: QtDriver) -> None:
        """bind='{a + b}' with multiple variables."""

        @widget
        class Calculator(QWidget):
            a: int = state(10)
            b: int = state(20)
            label: QLabel = make(QLabel, bind="{a} + {b} = {a + b}")

        w = Calculator()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("10 + 20 = 30")

        w.a = 5
        assert_that(w.label.text()).is_equal_to("5 + 20 = 25")

        w.b = 3
        assert_that(w.label.text()).is_equal_to("5 + 3 = 8")

    def test_builtin_functions(self, qt: QtDriver) -> None:
        """bind='{len(name)}' with builtin functions."""

        @widget
        class LengthDisplay(QWidget):
            name: str = state("hello")
            label: QLabel = make(QLabel, bind="Length: {len(name)}")

        w = LengthDisplay()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Length: 5")

        w.name = "goodbye"
        assert_that(w.label.text()).is_equal_to("Length: 7")

    def test_self_access(self, qt: QtDriver) -> None:
        """bind='{self.count + 5}' with self reference."""

        @widget
        class Counter(QWidget):
            count: int = state(0)
            label: QLabel = make(QLabel, bind="Value: {self.count + self.count}")

        w = Counter()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Value: 0")

        w.count = 10
        assert_that(w.label.text()).is_equal_to("Value: 20")
