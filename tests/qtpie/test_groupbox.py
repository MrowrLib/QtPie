# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnknownMemberType=false
"""Tests for @groupbox decorator and GroupBox base class.

This tests that GroupBox (QGroupBox + WidgetBase) works with the @groupbox decorator
(alias for @widget) to provide the same declarative features as Widget.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QCheckBox, QGroupBox, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout

from qtpie import GroupBox, Variable, Widget, groupbox, new, widget
from qtpie.testing import QtDriver


class TestGroupBoxBasics:
    """Basic GroupBox functionality."""

    def test_groupbox_is_qgroupbox(self, qt: QtDriver) -> None:
        """GroupBox should be a QGroupBox subclass."""

        @groupbox
        class TestGroupBox(GroupBox):
            pass

        instance = qt.track(TestGroupBox())
        assert_that(instance).is_instance_of(QGroupBox)
        assert_that(instance).is_instance_of(GroupBox)

    def test_groupbox_with_title(self, qt: QtDriver) -> None:
        """GroupBox should support title as first positional arg."""

        @groupbox("Settings")
        class TestGroupBox(GroupBox):
            _option: QCheckBox = new("Enable")

        instance = qt.track(TestGroupBox())
        assert_that(instance.title()).is_equal_to("Settings")

    def test_groupbox_with_widgets(self, qt: QtDriver) -> None:
        """GroupBox should support widget children like Widget does."""

        @groupbox("Options")
        class TestGroupBox(GroupBox):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

        instance = qt.track(TestGroupBox())

        assert_that(instance._label).is_instance_of(QLabel)
        assert_that(instance._label.text()).is_equal_to("Hello")
        assert_that(instance._button).is_instance_of(QPushButton)
        assert_that(instance._button.text()).is_equal_to("Click")

    def test_groupbox_with_layout(self, qt: QtDriver) -> None:
        """GroupBox should support layout configuration."""

        @groupbox("Items", layout="vertical")
        class TestGroupBox(GroupBox):
            _label1: QLabel = new("First")
            _label2: QLabel = new("Second")

        instance = qt.track(TestGroupBox())

        layout = instance.layout()
        assert_that(layout).is_instance_of(QVBoxLayout)
        assert_that(layout.count()).is_equal_to(2)

    def test_groupbox_no_layout(self, qt: QtDriver) -> None:
        """GroupBox with layout=None should not have automatic layout."""

        @groupbox(layout=None)
        class TestGroupBox(GroupBox):
            pass

        instance = qt.track(TestGroupBox())
        assert_that(instance.layout()).is_none()

    def test_groupbox_bare_decorator(self, qt: QtDriver) -> None:
        """@groupbox without parens should work."""

        @groupbox
        class TestGroupBox(GroupBox):
            _label: QLabel = new("Test")

        instance = qt.track(TestGroupBox())
        assert_that(instance._label.text()).is_equal_to("Test")


class TestGroupBoxProperties:
    """QGroupBox-specific properties."""

    def test_groupbox_checkable(self, qt: QtDriver) -> None:
        """GroupBox should support checkable via decorator kwargs."""

        @groupbox("Options", checkable=True)
        class TestGroupBox(GroupBox):
            _option: QCheckBox = new("Enable")

        instance = qt.track(TestGroupBox())
        assert_that(instance.isCheckable()).is_true()

    def test_groupbox_checked(self, qt: QtDriver) -> None:
        """GroupBox should support checked via decorator kwargs."""

        @groupbox("Options", checkable=True, checked=False)
        class TestGroupBox(GroupBox):
            _option: QCheckBox = new("Enable")

        instance = qt.track(TestGroupBox())
        assert_that(instance.isCheckable()).is_true()
        assert_that(instance.isChecked()).is_false()

    def test_groupbox_flat(self, qt: QtDriver) -> None:
        """GroupBox should support flat via decorator kwargs."""

        @groupbox("Options", flat=True)
        class TestGroupBox(GroupBox):
            _option: QCheckBox = new("Enable")

        instance = qt.track(TestGroupBox())
        assert_that(instance.isFlat()).is_true()

    def test_groupbox_alignment(self, qt: QtDriver) -> None:
        """GroupBox should support alignment via decorator kwargs."""
        from qtpy.QtCore import Qt

        @groupbox("Options", alignment=Qt.AlignmentFlag.AlignRight)
        class TestGroupBox(GroupBox):
            _option: QCheckBox = new("Enable")

        instance = qt.track(TestGroupBox())
        assert_that(instance.alignment()).is_equal_to(Qt.AlignmentFlag.AlignRight)


class TestGroupBoxVariables:
    """GroupBox with Variable support."""

    def test_groupbox_with_variable(self, qt: QtDriver) -> None:
        """GroupBox should support Variable fields."""

        @groupbox("Counter")
        class TestGroupBox(GroupBox):
            _count: Variable[int] = new(42)

        instance = qt.track(TestGroupBox())

        assert_that(instance._count.value).is_equal_to(42)
        instance._count.value = 100
        assert_that(instance._count.value).is_equal_to(100)

    def test_groupbox_with_variable_widget(self, qt: QtDriver) -> None:
        """GroupBox should support Variable[T, W] with auto-created widget."""

        @groupbox("Input")
        class TestGroupBox(GroupBox):
            _name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name")

        instance = qt.track(TestGroupBox())

        assert_that(instance._name.value).is_equal_to("default")
        assert_that(instance._name.widget).is_instance_of(QLineEdit)
        assert_that(instance._name.widget.placeholderText()).is_equal_to("Enter name")

    def test_groupbox_variable_binding(self, qt: QtDriver) -> None:
        """GroupBox should support binding Variables to widgets."""

        @groupbox("Display")
        class TestGroupBox(GroupBox):
            _message: Variable[str] = new("Hello")
            _label: QLabel = new(bind="{_message}")

        instance = qt.track(TestGroupBox())

        assert_that(instance._label.text()).is_equal_to("Hello")
        instance._message.value = "Updated"
        assert_that(instance._label.text()).is_equal_to("Updated")


class TestGroupBoxRecord:
    """GroupBox with record type (GroupBox[T])."""

    def test_groupbox_with_record_type(self, qt: QtDriver) -> None:
        """GroupBox[T] should support record type like Widget[T]."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @groupbox("Person")
        class PersonGroupBox(GroupBox[Person]):
            pass

        instance = qt.track(PersonGroupBox())
        instance.record = Person("Alice", 30)

        assert_that(instance.record.name).is_equal_to("Alice")
        assert_that(instance.record.age).is_equal_to(30)

    def test_groupbox_record_auto_binding(self, qt: QtDriver) -> None:
        """GroupBox[T] should auto-bind fields named same as record properties."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @groupbox("Edit Person", record=Person("Bob", 25))
        class PersonGroupBox(GroupBox[Person]):
            name: QLineEdit = new()
            age: QSpinBox = new()

        instance = qt.track(PersonGroupBox())

        # Fields should be bound to record
        assert_that(instance.name.text()).is_equal_to("Bob")
        assert_that(instance.age.value()).is_equal_to(25)

        # Changing record should update fields
        instance.record.name = "Charlie"
        assert_that(instance.name.text()).is_equal_to("Charlie")

    def test_groupbox_record_dirty_tracking(self, qt: QtDriver) -> None:
        """GroupBox should support dirty tracking from WidgetBase."""

        @dataclass
        class Person:
            name: str = ""

        @groupbox("Person", record=Person("Original"))
        class PersonGroupBox(GroupBox[Person]):
            name: QLineEdit = new()

        instance = qt.track(PersonGroupBox())

        assert_that(instance.is_dirty.get()).is_false()
        instance.record.name = "Changed"
        assert_that(instance.is_dirty.get()).is_true()

        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()


class TestGroupBoxSetup:
    """GroupBox lifecycle hooks."""

    def test_groupbox_setup_hook(self, qt: QtDriver) -> None:
        """GroupBox should call __setup__ after initialization."""
        setup_called = []

        @groupbox("Test")
        class TestGroupBox(GroupBox):
            _label: QLabel = new("Before")

            def __setup__(self) -> None:
                setup_called.append(True)
                self._label.setText("After")

        instance = qt.track(TestGroupBox())

        assert_that(setup_called).is_length(1)
        assert_that(instance._label.text()).is_equal_to("After")


class TestGroupBoxNesting:
    """GroupBox used as child component."""

    def test_groupbox_in_widget(self, qt: QtDriver) -> None:
        """GroupBox should work as a child component in a Widget."""

        @groupbox("Card Settings")
        class SettingsBox(GroupBox):
            _option1: QCheckBox = new("Enable feature")
            _option2: QCheckBox = new("Show tips")

        @widget
        class MyWidget(Widget):
            _header: QLabel = new("Header")
            _settings: SettingsBox = new()
            _footer: QLabel = new("Footer")

        instance = qt.track(MyWidget())

        assert_that(instance._settings).is_instance_of(SettingsBox)
        assert_that(instance._settings).is_instance_of(QGroupBox)
        assert_that(instance._settings.title()).is_equal_to("Card Settings")
        assert_that(instance._settings._option1.text()).is_equal_to("Enable feature")

    def test_nested_groupboxes(self, qt: QtDriver) -> None:
        """GroupBoxes should be nestable."""

        @groupbox("Inner")
        class InnerGroupBox(GroupBox):
            _inner_label: QLabel = new("Inner content")

        @groupbox("Outer")
        class OuterGroupBox(GroupBox):
            _outer_label: QLabel = new("Outer content")
            _inner: InnerGroupBox = new()

        instance = qt.track(OuterGroupBox())

        assert_that(instance.title()).is_equal_to("Outer")
        assert_that(instance._inner.title()).is_equal_to("Inner")
        assert_that(instance._outer_label.text()).is_equal_to("Outer content")
        assert_that(instance._inner._inner_label.text()).is_equal_to("Inner content")


class TestGroupBoxSignals:
    """GroupBox signal connections."""

    def test_groupbox_signal_connection(self, qt: QtDriver) -> None:
        """GroupBox should support signal connections like Widget."""
        clicked_count = []

        @groupbox("Actions")
        class TestGroupBox(GroupBox):
            _button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                clicked_count.append(1)

        instance = qt.track(TestGroupBox())
        instance._button.click()

        assert_that(clicked_count).is_length(1)

    def test_groupbox_toggled_signal(self, qt: QtDriver) -> None:
        """GroupBox should support toggled signal for checkable boxes."""
        toggled_values = []

        @groupbox("Options", checkable=True, checked=True, toggled="on_toggled")
        class TestGroupBox(GroupBox):
            _option: QCheckBox = new("Enable")

            def on_toggled(self, checked: bool) -> None:
                toggled_values.append(checked)

        instance = qt.track(TestGroupBox())
        instance.setChecked(False)

        assert_that(toggled_values).is_length(1)
        assert_that(toggled_values[0]).is_false()


class TestGroupBoxObjectName:
    """GroupBox objectName and CSS classes."""

    def test_groupbox_object_name(self, qt: QtDriver) -> None:
        """GroupBox should support name= for objectName."""

        @groupbox("Settings", name="settings-box")
        class TestGroupBox(GroupBox):
            pass

        instance = qt.track(TestGroupBox())
        assert_that(instance.objectName()).is_equal_to("settings-box")

    def test_groupbox_css_classes(self, qt: QtDriver) -> None:
        """GroupBox should support classes= for CSS classes."""

        @groupbox("Settings", classes=["primary", "bordered"])
        class TestGroupBox(GroupBox):
            pass

        instance = qt.track(TestGroupBox())
        # CSS classes are stored in property()
        classes = instance.property("class")
        assert_that(classes).contains("primary")
        assert_that(classes).contains("bordered")

    def test_groupbox_default_object_name(self, qt: QtDriver) -> None:
        """GroupBox without name= should use class name as objectName."""

        @groupbox
        class MyCustomGroupBox(GroupBox):
            pass

        instance = qt.track(MyCustomGroupBox())
        assert_that(instance.objectName()).is_equal_to("MyCustomGroupBox")


class TestGroupBoxValidation:
    """GroupBox validation support."""

    def test_groupbox_is_valid(self, qt: QtDriver) -> None:
        """GroupBox should support is_valid from WidgetBase."""

        @groupbox("Form")
        class TestGroupBox(GroupBox):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name required")

        instance = qt.track(TestGroupBox())

        # Empty name should be invalid
        assert_that(instance.is_valid.get()).is_false()

        # Set name should be valid
        instance._name.value = "Test"
        assert_that(instance.is_valid.get()).is_true()

    def test_groupbox_validation_errors(self, qt: QtDriver) -> None:
        """GroupBox should expose validation_error_messages."""

        @groupbox("Form")
        class TestGroupBox(GroupBox):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name is required")

        instance = qt.track(TestGroupBox())

        errors = instance.validation_error_messages.get()
        assert_that(errors).contains("Name is required")


class TestGroupBoxRequiresDecorator:
    """GroupBox should require @groupbox decorator."""

    def test_groupbox_without_decorator_raises(self, qt: QtDriver) -> None:
        """Instantiating GroupBox without @groupbox should raise TypeError."""

        class UndecoratedGroupBox(GroupBox):
            pass

        with pytest.raises(TypeError, match="must be decorated with @groupbox"):
            UndecoratedGroupBox()
