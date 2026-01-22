# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for special placeholders (#widget, #window, #app, #var, #index, #key, #value, #args, #record).

This file tests placeholder support across three main binding functions:
1. create_format_binding() - for bind="" parameters
2. create_expression_binding() - for visible="", enabled="" parameters
3. create_signal_expression_handler() - for signal handlers like clicked=""

Each placeholder is tested for:
- Format bindings (bind="Hello {#widget.name}")
- Expression bindings (visible="{#widget.is_visible}")
- Signal handler expressions (clicked="{#widget.do_something()}")
- Signal handler statements (clicked="{#widget.count += 1}")
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import (
    RECORD_CLASS_TYPES,
    WIDGET_CLASS_TYPES,
    WINDOW_CLASS_TYPES,
    create_and_track,
    get_main_window,
)

# =============================================================================
# Test Fixtures - Shared dataclasses for record tests
# =============================================================================


@dataclass
class Person:
    """Simple record for testing #record placeholder."""

    name: str = "Alice"
    age: int = 30
    is_active: bool = True


@dataclass
class Counter:
    """Record with mutable counter for statement tests."""

    count: int = 0


# =============================================================================
# #widget Placeholder Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestWidgetPlaceholder:
    """Test {#widget} placeholder in format/expression bindings and signals."""

    def test_format_binding_widget_objectname(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#widget.objectName()}' accesses widget method."""
        from qtpie import AppBase

        if base_class is AppBase:
            pytest.skip("AppBase is not a QWidget, so #widget doesn't work")

        @decorator(name="my-widget")
        class TestClass(base_class):
            _label: QLabel = new(bind="{#widget.objectName()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("my-widget")

    def test_format_binding_widget_property(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#widget.my_prop}' accesses widget property."""

        @decorator
        class TestClass(base_class):
            my_prop: str = "hello-world"
            _label: QLabel = new(bind="{#widget.my_prop}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("hello-world")

    def test_format_binding_widget_method(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#widget.get_greeting()}' calls widget method."""

        @decorator
        class TestClass(base_class):
            _label: QLabel = new(bind="{#widget.get_greeting()}")

            def get_greeting(self) -> str:
                return "Hello from widget!"

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Hello from widget!")

    def test_expression_binding_widget_bool_property(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#widget.show_label}' uses widget property for visibility."""

        @decorator
        class TestClass(base_class):
            show_label: bool = True
            _label: QLabel = new("Visible!", visible="{#widget.show_label}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_true()

    def test_expression_binding_widget_method_bool(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#widget.should_show()}' calls widget method for visibility."""

        @decorator
        class TestClass(base_class):
            _label: QLabel = new("Visible!", visible="{#widget.should_show()}")

            def should_show(self) -> bool:
                return False

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_false()


# Note: Using WIDGET_CLASS_TYPES instead of SIGNAL_CLASS_TYPES because
# Menu doesn't support QPushButton children the same way
@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestWidgetPlaceholderSignals:
    """Test {#widget} placeholder in signal handlers."""

    def test_signal_expression_widget_method(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{#widget.on_click()}' calls widget method."""
        from qtpie import AppBase

        if base_class is AppBase:
            pytest.skip("AppBase is not a QWidget, so #widget doesn't work in signals")

        call_count = {"value": 0}

        @decorator
        class TestClass(base_class):
            _button: QPushButton = new("Click", clicked="{#widget.on_click()}")

            def on_click(self) -> None:
                call_count["value"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance._button.click()
        assert_that(call_count["value"]).is_equal_to(1)

    def test_signal_statement_widget_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{#widget._count += 1}' increments widget variable."""
        from qtpie import AppBase

        if base_class is AppBase:
            pytest.skip("AppBase is not a QWidget, so #widget doesn't work in signals")

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            _button: QPushButton = new("Click", clicked="{#widget._count += 1}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.value).is_equal_to(0)
        instance._button.click()
        assert_that(instance._count.value).is_equal_to(1)
        instance._button.click()
        assert_that(instance._count.value).is_equal_to(2)


# =============================================================================
# #window Placeholder Tests (Window and App only)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WINDOW_CLASS_TYPES)
class TestWindowPlaceholder:
    """Test {#window} placeholder (alias for #widget on Window/App)."""

    def test_format_binding_window_title(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#window.windowTitle()}' accesses window title."""
        from qtpie import AppBase

        if base_class is AppBase:
            pytest.skip("AppBase's children don't have #window - use #app instead")

        @decorator(title="My Window Title")
        class TestClass(base_class):
            _label: QLabel = new(bind="{#window.windowTitle()}")

        instance = create_and_track(qt, TestClass, base_class)
        get_main_window(instance, base_class)  # Ensure window is properly tracked
        # The label should show the window title
        assert_that(instance._label.text()).is_equal_to("My Window Title")

    def test_format_binding_window_property(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#window.my_prop}' accesses window property."""

        @decorator(title="Test")
        class TestClass(base_class):
            my_prop: str = "window-property"
            _label: QLabel = new(bind="{#window.my_prop}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("window-property")

    def test_expression_binding_window_bool(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#window.show_content}' uses window property."""

        @decorator(title="Test")
        class TestClass(base_class):
            show_content: bool = False
            _label: QLabel = new("Content", visible="{#window.show_content}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_false()


# =============================================================================
# #app Placeholder Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestAppPlaceholder:
    """Test {#app} placeholder for accessing QApplication instance."""

    def test_format_binding_app_name(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#app.applicationName()}' accesses app name."""
        from PySide6.QtWidgets import QApplication

        # Set app name for test
        app = QApplication.instance()
        assert app is not None
        old_name = app.applicationName()
        app.setApplicationName("TestAppName")

        try:

            @decorator
            class TestClass(base_class):
                _label: QLabel = new(bind="{#app.applicationName()}")

            instance = create_and_track(qt, TestClass, base_class)
            assert_that(instance._label.text()).is_equal_to("TestAppName")
        finally:
            app.setApplicationName(old_name)

    def test_expression_binding_app_property(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#app is not None}' checks app existence."""

        @decorator
        class TestClass(base_class):
            _label: QLabel = new("App exists!", visible="{#app is not None}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_true()


# =============================================================================
# #var Placeholder Tests (Variable[T, W] context)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVarPlaceholder:
    """Test {#var} placeholder in Variable[T, W] context."""

    def test_var_simple_display(self, base_class, decorator, qt: QtDriver) -> None:
        """{#var} displays Variable's value."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int, QLabel] = new(42)(bind="Count: {#var}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.widget.text()).is_equal_to("Count: 42")

    def test_var_with_math(self, base_class, decorator, qt: QtDriver) -> None:
        """{#var * 2} does math on Variable's value."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.widget.text()).is_equal_to("Double: 20")

    def test_var_with_string_method(self, base_class, decorator, qt: QtDriver) -> None:
        """{#var.upper()} calls method on Variable's value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLabel] = new("hello")(bind="Upper: {#var.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.text()).is_equal_to("Upper: HELLO")

    def test_var_reactivity(self, base_class, decorator, qt: QtDriver) -> None:
        """{#var} updates when Variable changes."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int, QLabel] = new(0)(bind="Value: {#var}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.widget.text()).is_equal_to("Value: 0")

        instance._count.value = 100
        assert_that(instance._count.widget.text()).is_equal_to("Value: 100")


# =============================================================================
# #index Placeholder Tests (List Repeaters)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestIndexPlaceholder:
    """Test {#index} placeholder in list repeaters."""

    def test_index_in_list_repeater(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] with format='{#index}: {#self}' shows indices."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b", "c"])
            _labels: list[QLabel] = new(bind="_items", format="{#index}: {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(len(instance._labels)).is_equal_to(3)
        assert_that(instance._labels[0].text()).is_equal_to("0: a")
        assert_that(instance._labels[1].text()).is_equal_to("1: b")
        assert_that(instance._labels[2].text()).is_equal_to("2: c")

    @pytest.mark.xfail(reason="Index update on insert not yet implemented - existing feature gap")
    def test_index_updates_on_insert(self, base_class, decorator, qt: QtDriver) -> None:
        """Indices update when items are inserted."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b"])
            _labels: list[QLabel] = new(bind="_items", format="[{#index}] {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels[0].text()).is_equal_to("[0] a")
        assert_that(instance._labels[1].text()).is_equal_to("[1] b")

        # Insert at beginning
        instance._items.observable.insert(0, "new")  # type: ignore[union-attr]
        assert_that(instance._labels[0].text()).is_equal_to("[0] new")
        assert_that(instance._labels[1].text()).is_equal_to("[1] a")
        assert_that(instance._labels[2].text()).is_equal_to("[2] b")

    def test_index_with_object_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Index works with object items."""

        @decorator
        class TestClass(base_class):
            _people: Variable[list[Person]] = new(default=[Person("Alice", 30), Person("Bob", 25)])
            _labels: list[QLabel] = new(bind="_people", format="{#index}. {name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels[0].text()).is_equal_to("0. Alice")
        assert_that(instance._labels[1].text()).is_equal_to("1. Bob")


# =============================================================================
# #key and #value Placeholder Tests (Dict Repeaters)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestKeyValuePlaceholders:
    """Test {#key} and {#value} placeholders in dict repeaters."""

    def test_key_value_simple_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """Dict repeater with format='{#key} = {#value}'."""

        @decorator
        class TestClass(base_class):
            _scores: Variable[dict[str, int]] = new(default={"Alice": 100, "Bob": 85})
            _labels: list[QLabel] = new(bind="_scores", format="{#key} = {#value}")

        instance = create_and_track(qt, TestClass, base_class)
        texts = [label.text() for label in instance._labels]
        assert_that(texts).contains("Alice = 100")
        assert_that(texts).contains("Bob = 85")

    def test_key_value_object_values(self, base_class, decorator, qt: QtDriver) -> None:
        """Dict repeater with object values: format='{#key}: {name}'."""

        @decorator
        class TestClass(base_class):
            _people: Variable[dict[str, Person]] = new(default={"p1": Person("Alice", 30), "p2": Person("Bob", 25)})
            _labels: list[QLabel] = new(bind="_people", format="{#key}: {name}, age {age}")

        instance = create_and_track(qt, TestClass, base_class)
        texts = [label.text() for label in instance._labels]
        assert_that(texts).contains("p1: Alice, age 30")
        assert_that(texts).contains("p2: Bob, age 25")

    @pytest.mark.xfail(reason="Method calls on #key placeholder not yet implemented")
    def test_key_with_method(self, base_class, decorator, qt: QtDriver) -> None:
        """Dict repeater with {#key.upper()}."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"foo": 1, "bar": 2})
            _labels: list[QLabel] = new(bind="_data", format="{#key.upper()}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)
        texts = [label.text() for label in instance._labels]
        assert_that(texts).contains("FOO: 1")
        assert_that(texts).contains("BAR: 2")


# =============================================================================
# #args Placeholder Tests (Signal Handlers)
# =============================================================================


# Note: Using WIDGET_CLASS_TYPES because Menu doesn't support QLineEdit/QPushButton children
@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestArgsPlaceholder:
    """Test {#args} placeholder in signal handlers."""

    def test_args_with_textchanged(self, base_class, decorator, qt: QtDriver) -> None:
        """textChanged='{on_text(#args)}' passes signal argument."""
        received_text: list[str] = []

        @decorator
        class TestClass(base_class):
            _input: QLineEdit = new(textChanged="{on_text_changed(#args)}")

            def on_text_changed(self, text: str) -> None:
                received_text.append(text)

        instance = create_and_track(qt, TestClass, base_class)
        instance._input.setText("hello")
        assert_that(received_text).is_equal_to(["hello"])

    def test_args_with_no_args_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{on_click(#args)}' works with no-arg signal."""
        call_count = {"value": 0}

        @decorator
        class TestClass(base_class):
            _button: QPushButton = new("Click", clicked="{on_click(#args)}")

            def on_click(self) -> None:
                call_count["value"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance._button.click()
        assert_that(call_count["value"]).is_equal_to(1)


# =============================================================================
# Signal Expression vs Statement Tests
# =============================================================================


# Note: Using WIDGET_CLASS_TYPES because Menu doesn't support QPushButton children
@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSignalExpressions:
    """Test expression vs statement code paths in signal handlers."""

    def test_expression_method_call(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{on_click()}' is an expression (method call)."""
        call_count = {"value": 0}

        @decorator
        class TestClass(base_class):
            _button: QPushButton = new("Click", clicked="{on_click()}")

            def on_click(self) -> None:
                call_count["value"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance._button.click()
        assert_that(call_count["value"]).is_equal_to(1)

    def test_statement_simple_assignment(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{_count = 42}' is a statement (assignment)."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            _button: QPushButton = new("Click", clicked="{_count = 42}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.value).is_equal_to(0)
        instance._button.click()
        assert_that(instance._count.value).is_equal_to(42)

    def test_statement_augmented_assignment_add(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{_count += 1}' is a statement (augmented assignment)."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)
            _button: QPushButton = new("Click", clicked="{_count += 5}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.value).is_equal_to(10)
        instance._button.click()
        assert_that(instance._count.value).is_equal_to(15)

    def test_statement_augmented_assignment_subtract(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{_count -= 1}' is a statement (augmented assignment)."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)
            _button: QPushButton = new("Click", clicked="{_count -= 3}")

        instance = create_and_track(qt, TestClass, base_class)
        instance._button.click()
        assert_that(instance._count.value).is_equal_to(7)

    def test_statement_augmented_assignment_multiply(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{_count *= 2}' is a statement (augmented assignment)."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(5)
            _button: QPushButton = new("Click", clicked="{_count *= 2}")

        instance = create_and_track(qt, TestClass, base_class)
        instance._button.click()
        assert_that(instance._count.value).is_equal_to(10)


# =============================================================================
# #record Placeholder Tests (Widget[T], Window[T], etc.)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestRecordPlaceholder:
    """Test {#record} placeholder for accessing record in Widget[T], Window[T], etc."""

    def test_format_binding_record_field(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='Name: {#record.name}' displays record field."""

        @decorator(record=Person("Alice", 30))
        class TestClass(base_class[Person]):
            _label: QLabel = new(bind="Name: {#record.name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Name: Alice")

    def test_format_binding_record_method(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#record.name.upper()}' calls method on record field."""

        @decorator(record=Person("alice", 25))
        class TestClass(base_class[Person]):
            _label: QLabel = new(bind="Upper: {#record.name.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Upper: ALICE")

    def test_format_binding_record_multiple_fields(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='{#record.name}, age {#record.age}' displays multiple fields."""

        @decorator(record=Person("Bob", 35))
        class TestClass(base_class[Person]):
            _label: QLabel = new(bind="{#record.name}, age {#record.age}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Bob, age 35")

    def test_expression_binding_record_not_none(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#record is not None}' checks if record exists."""

        @decorator(record=Person())
        class TestClass(base_class[Person]):
            _label: QLabel = new("Has record!", visible="{#record is not None}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_true()

    def test_expression_binding_record_is_none(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#record is not None}' is False when record is None."""

        # Don't provide a record - it should be None
        @decorator
        class TestClass(base_class[Person | None]):
            _label: QLabel = new("Has record!", visible="{#record is not None}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        # Record is None, so label should be hidden
        assert_that(instance._label.isVisible()).is_false()

    def test_expression_binding_record_bool_field(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#record.is_active}' uses record bool field for visibility."""

        @decorator(record=Person("Test", 20, is_active=True))
        class TestClass(base_class[Person]):
            _label: QLabel = new("Active!", visible="{#record.is_active}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_true()

    def test_expression_binding_record_comparison(self, base_class, decorator, qt: QtDriver) -> None:
        """visible='{#record.age >= 18}' uses record field in comparison."""

        @decorator(record=Person("Adult", 25))
        class TestClass(base_class[Person]):
            _label: QLabel = new("Adult!", visible="{#record.age >= 18}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_true()


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestRecordPlaceholderSignals:
    """Test {#record} placeholder in signal handlers for classes that support records."""

    def test_signal_expression_record_method(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{#record.save()}' calls method on record."""
        call_count = {"value": 0}

        @dataclass
        class SaveableRecord:
            name: str = "test"

            def save(self) -> None:
                call_count["value"] += 1

        @decorator(record=SaveableRecord())
        class TestClass(base_class[SaveableRecord]):
            _button: QPushButton = new("Save", clicked="{#record.save()}")

        instance = create_and_track(qt, TestClass, base_class)
        instance._button.click()
        assert_that(call_count["value"]).is_equal_to(1)


# =============================================================================
# #record Reactivity Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestRecordReactivity:
    """Test that #record bindings are reactive (update when record changes)."""

    def test_format_binding_updates_on_record_change(self, base_class, decorator, qt: QtDriver) -> None:
        """Label updates when record field changes."""

        @decorator(record=Person("Alice", 30))
        class TestClass(base_class[Person]):
            _label: QLabel = new(bind="Name: {#record.name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._label.text()).is_equal_to("Name: Alice")

        # Change the record field
        instance.record.name = "Bob"
        assert_that(instance._label.text()).is_equal_to("Name: Bob")

    def test_expression_binding_updates_on_record_change(self, base_class, decorator, qt: QtDriver) -> None:
        """Visibility updates when record field changes."""

        @decorator(record=Person("Test", 20, is_active=True))
        class TestClass(base_class[Person]):
            _label: QLabel = new("Active!", visible="{#record.is_active}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.show()  # Must show parent for isVisible() to work
        assert_that(instance._label.isVisible()).is_true()

        # Change the record field
        instance.record.is_active = False
        assert_that(instance._label.isVisible()).is_false()
