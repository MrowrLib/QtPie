# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for CSS classes and object names across Widget, Window, and App.

Tests name= and classes= parameters on decorators and new().
Menu is excluded as it doesn't support child widgets with these properties.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from qtpie import Variable, new
from qtpie.styles import get_classes
from qtpie.testing import QtDriver

from .conftest import QWIDGET_CLASS_TYPES, WIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# Decorator name= and classes=
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestDecoratorNameClasses:
    """@decorator(name=..., classes=[...]) parameters.

    Uses QWIDGET_CLASS_TYPES since App is not a QWidget and doesn't have objectName().
    """

    def test_decorator_sets_object_name(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(name=...) sets objectName on the widget."""

        @decorator(name="my-widget")
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.objectName()).is_equal_to("my-widget")

    def test_decorator_sets_css_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(classes=[...]) sets CSS classes."""

        @decorator(classes=["card", "primary"])
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance)).is_equal_to(["card", "primary"])

    def test_decorator_sets_both_name_and_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(name=..., classes=[...]) sets both."""

        @decorator(name="styled-card", classes=["card", "elevated"])
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.objectName()).is_equal_to("styled-card")
        assert_that(get_classes(instance)).is_equal_to(["card", "elevated"])

    def test_default_object_name_is_class_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Without name=, objectName defaults to class name."""

        @decorator
        class MyCustomClassName(base_class):
            pass

        instance = create_and_track(qt, MyCustomClassName, base_class)
        assert_that(instance.objectName()).is_equal_to("MyCustomClassName")


# =============================================================================
# Field name= and classes=
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFieldNameClasses:
    """new(name=..., classes=[...]) on QWidget fields."""

    def test_field_sets_object_name(self, base_class, decorator, qt: QtDriver) -> None:
        """new(name=...) sets objectName on field widget."""

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", name="action-button")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button.objectName()).is_equal_to("action-button")

    def test_field_sets_css_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """new(classes=[...]) sets CSS classes on field widget."""

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", classes=["btn", "btn-primary"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance.button)).is_equal_to(["btn", "btn-primary"])

    def test_field_sets_both_name_and_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """new(name=..., classes=[...]) sets both on field widget."""

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Hello", name="greeting", classes=["text", "large"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.label.objectName()).is_equal_to("greeting")
        assert_that(get_classes(instance.label)).is_equal_to(["text", "large"])

    def test_field_default_object_name_is_widget_class_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Without name=, objectName defaults to widget class name, field stores field name."""
        from qtpie.styles import get_field_property

        @decorator
        class TestClass(base_class):
            my_button: QPushButton = new("Click")
            my_label: QLabel = new("Text")

        instance = create_and_track(qt, TestClass, base_class)
        # objectName defaults to widget class name
        assert_that(instance.my_button.objectName()).is_equal_to("QPushButton")
        assert_that(instance.my_label.objectName()).is_equal_to("QLabel")
        # field property stores the field name
        assert_that(get_field_property(instance.my_button)).is_equal_to("my_button")
        assert_that(get_field_property(instance.my_label)).is_equal_to("my_label")


# =============================================================================
# Variable[T, W] name= and classes=
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVariableWidgetNameClasses:
    """Variable[T, W] = new(...)(name=..., classes=[...])."""

    def test_variable_widget_sets_object_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, QLineEdit] = new(...)(name=...) sets objectName."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("initial")(name="name-input")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.objectName()).is_equal_to("name-input")

    def test_variable_widget_sets_css_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[str, QLineEdit] = new(...)(classes=[...]) sets classes."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("initial")(classes=["input", "bordered"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance._name.widget)).is_equal_to(["input", "bordered"])

    def test_variable_widget_sets_both(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] with both name= and classes=."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("initial")(name="name-field", classes=["input"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.widget.objectName()).is_equal_to("name-field")
        assert_that(get_classes(instance._name.widget)).is_equal_to(["input"])

    def test_variable_widget_default_object_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] without name= defaults to widget class name for objectName."""
        from qtpie.styles import get_field_property

        @decorator
        class TestClass(base_class):
            my_field: Variable[str, QLineEdit] = new("initial")

        instance = create_and_track(qt, TestClass, base_class)
        # objectName defaults to widget class name
        assert_that(instance.my_field.widget.objectName()).is_equal_to("QLineEdit")
        # field property stores the field name
        assert_that(get_field_property(instance.my_field.widget)).is_equal_to("my_field")


# =============================================================================
# Multiple Widgets
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMultipleWidgetStyles:
    """Multiple widgets with various styling."""

    def test_multiple_widgets_different_names(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple widgets can have different object names."""

        @decorator
        class TestClass(base_class):
            header: QLabel = new("Header", name="page-header")
            content: QLabel = new("Content", name="main-content")
            footer: QLabel = new("Footer", name="page-footer")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.header.objectName()).is_equal_to("page-header")
        assert_that(instance.content.objectName()).is_equal_to("main-content")
        assert_that(instance.footer.objectName()).is_equal_to("page-footer")

    def test_multiple_widgets_different_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple widgets can have different CSS classes."""

        @decorator
        class TestClass(base_class):
            primary: QPushButton = new("Primary", classes=["btn", "btn-primary"])
            secondary: QPushButton = new("Secondary", classes=["btn", "btn-secondary"])
            danger: QPushButton = new("Delete", classes=["btn", "btn-danger"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance.primary)).is_equal_to(["btn", "btn-primary"])
        assert_that(get_classes(instance.secondary)).is_equal_to(["btn", "btn-secondary"])
        assert_that(get_classes(instance.danger)).is_equal_to(["btn", "btn-danger"])


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestMixedStyledAndUnstyled:
    """Mix of styled and unstyled widgets.

    Uses QWIDGET_CLASS_TYPES since test accesses instance.objectName().
    """

    def test_mixed_styled_and_unstyled(self, base_class, decorator, qt: QtDriver) -> None:
        """Mix of styled and unstyled widgets.

        When @decorator(name=...) is set, it propagates to children without explicit name=.
        """

        @decorator(name="my-form")
        class TestClass(base_class):
            styled: QLabel = new("Styled", name="custom", classes=["styled"])
            unstyled: QLabel = new("Unstyled")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.objectName()).is_equal_to("my-form")
        # Explicit name= overrides decorator name
        assert_that(instance.styled.objectName()).is_equal_to("custom")
        assert_that(get_classes(instance.styled)).is_equal_to(["styled"])
        # No explicit name=, so inherits decorator name
        assert_that(instance.unstyled.objectName()).is_equal_to("my-form")
        assert_that(get_classes(instance.unstyled)).is_equal_to([])


# =============================================================================
# Empty Classes
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestEmptyClasses:
    """Empty classes list behavior.

    Uses QWIDGET_CLASS_TYPES since tests access get_classes(instance).
    """

    def test_empty_classes_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty classes= list results in empty classes."""

        @decorator(classes=[])
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance)).is_equal_to([])

    def test_no_classes_results_in_empty_list(self, base_class, decorator, qt: QtDriver) -> None:
        """No classes= results in empty list."""

        @decorator
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance)).is_equal_to([])


# =============================================================================
# Single Class
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestSingleClassOnDecorator:
    """Single CSS class on decorator.

    Uses QWIDGET_CLASS_TYPES since test accesses get_classes(instance).
    """

    def test_single_class_in_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Single class in list works."""

        @decorator(classes=["solo"])
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance)).is_equal_to(["solo"])


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSingleClassOnField:
    """Single CSS class on field widget."""

    def test_single_class_on_field(self, base_class, decorator, qt: QtDriver) -> None:
        """Single class on field widget."""

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", classes=["primary"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_classes(instance.button)).is_equal_to(["primary"])


# =============================================================================
# Leading Underscore Stripping
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLeadingUnderscoreStripping:
    """Leading underscore is stripped from field names for field property."""

    def test_underscore_stripped_from_field_name(self, base_class, decorator, qt: QtDriver) -> None:
        """_button gets field property 'button' (not '_button'), objectName is class name."""
        from qtpie.styles import get_field_property

        @decorator
        class TestClass(base_class):
            _button: QPushButton = new("Click")
            _label: QLabel = new("Text")

        instance = create_and_track(qt, TestClass, base_class)
        # objectName defaults to widget class name
        assert_that(instance._button.objectName()).is_equal_to("QPushButton")
        assert_that(instance._label.objectName()).is_equal_to("QLabel")
        # field property has the stripped field name
        assert_that(get_field_property(instance._button)).is_equal_to("button")
        assert_that(get_field_property(instance._label)).is_equal_to("label")

    def test_no_underscore_unchanged(self, base_class, decorator, qt: QtDriver) -> None:
        """Fields without underscore keep their name as-is in field property."""
        from qtpie.styles import get_field_property

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click")
            myLabel: QLabel = new("Text")

        instance = create_and_track(qt, TestClass, base_class)
        # objectName defaults to widget class name
        assert_that(instance.button.objectName()).is_equal_to("QPushButton")
        assert_that(instance.myLabel.objectName()).is_equal_to("QLabel")
        # field property has the field name unchanged
        assert_that(get_field_property(instance.button)).is_equal_to("button")
        assert_that(get_field_property(instance.myLabel)).is_equal_to("myLabel")

    def test_variable_widget_underscore_stripped(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] with underscore prefix gets stripped field property."""
        from qtpie.styles import get_field_property

        @decorator
        class TestClass(base_class):
            _name: Variable[str, QLineEdit] = new("initial")

        instance = create_and_track(qt, TestClass, base_class)
        # objectName defaults to widget class name
        assert_that(instance._name.widget.objectName()).is_equal_to("QLineEdit")
        # field property has the stripped field name
        assert_that(get_field_property(instance._name.widget)).is_equal_to("name")


# =============================================================================
# Decorator Name Inheritance Priority
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDecoratorNameInheritance:
    """@decorator(name=...) propagates to children as fallback."""

    def test_decorator_name_inherited_by_children(self, base_class, decorator, qt: QtDriver) -> None:
        """Children without explicit name= inherit @decorator(name=...)."""

        @decorator(name="form-container")
        class TestClass(base_class):
            _button: QPushButton = new("Click")
            _label: QLabel = new("Text")

        instance = create_and_track(qt, TestClass, base_class)
        # All children inherit decorator name
        assert_that(instance._button.objectName()).is_equal_to("form-container")
        assert_that(instance._label.objectName()).is_equal_to("form-container")

    def test_explicit_name_overrides_decorator(self, base_class, decorator, qt: QtDriver) -> None:
        """new(name=...) overrides @decorator(name=...)."""

        @decorator(name="form-container")
        class TestClass(base_class):
            explicit: QPushButton = new("Click", name="custom-button")
            inherited: QLabel = new("Text")

        instance = create_and_track(qt, TestClass, base_class)
        # Explicit name wins
        assert_that(instance.explicit.objectName()).is_equal_to("custom-button")
        # No explicit name, inherits decorator
        assert_that(instance.inherited.objectName()).is_equal_to("form-container")

    def test_variable_widget_inherits_decorator_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] without name= inherits @decorator(name=...)."""

        @decorator(name="form-container")
        class TestClass(base_class):
            _input: Variable[str, QLineEdit] = new("initial")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._input.widget.objectName()).is_equal_to("form-container")

    def test_variable_widget_explicit_overrides_decorator(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] with explicit name= overrides @decorator(name=...)."""

        @decorator(name="form-container")
        class TestClass(base_class):
            _input: Variable[str, QLineEdit] = new("initial")(name="custom-input")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._input.widget.objectName()).is_equal_to("custom-input")

    def test_no_decorator_name_uses_widget_class_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Without @decorator(name=...), widget class name is used for objectName."""
        from qtpie.styles import get_field_property

        @decorator
        class TestClass(base_class):
            _button: QPushButton = new("Click")
            label: QLabel = new("Text")

        instance = create_and_track(qt, TestClass, base_class)
        # objectName defaults to widget class name
        assert_that(instance._button.objectName()).is_equal_to("QPushButton")
        assert_that(instance.label.objectName()).is_equal_to("QLabel")
        # field property stores the field name (stripped)
        assert_that(get_field_property(instance._button)).is_equal_to("button")
        assert_that(get_field_property(instance.label)).is_equal_to("label")


# =============================================================================
# Reactive CSS Classes (format string bindings)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestReactiveCssClasses:
    """CSS classes with format string bindings that update reactively."""

    def test_class_with_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """classes=["method-{_method}"] updates when variable changes."""

        @decorator
        class TestClass(base_class):
            _method: Variable[str] = new("GET")
            _label: QLabel = new("Request", classes=["badge", "method-{_method}"])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        assert_that(get_classes(instance._label)).contains("badge", "method-GET")

        # Change the variable - class should update reactively
        instance._method.value = "POST"
        qt.process_events()

        assert_that(get_classes(instance._label)).contains("badge", "method-POST")
        assert_that(get_classes(instance._label)).does_not_contain("method-GET")

    def test_class_with_record_field_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """classes=["status-{status}"] works with Widget[T] record fields."""
        from dataclasses import dataclass

        @dataclass
        class Item:
            name: str
            status: str

        @decorator(record=Item("Test", "active"))
        class TestClass(base_class[Item]):
            _label: QLabel = new(bind="{name}", classes=["item", "status-{status}"])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        assert_that(get_classes(instance._label)).contains("item", "status-active")

        # Change record field - class should update
        instance.record.status = "inactive"
        qt.process_events()

        assert_that(get_classes(instance._label)).contains("item", "status-inactive")
        assert_that(get_classes(instance._label)).does_not_contain("status-active")

    def test_multiple_dynamic_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple classes can have bindings."""

        @decorator
        class TestClass(base_class):
            _size: Variable[str] = new("large")
            _color: Variable[str] = new("blue")
            _label: QLabel = new("Styled", classes=["btn", "size-{_size}", "color-{_color}"])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        assert_that(get_classes(instance._label)).contains("btn", "size-large", "color-blue")

        instance._size.value = "small"
        instance._color.value = "red"
        qt.process_events()

        assert_that(get_classes(instance._label)).contains("btn", "size-small", "color-red")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestReactiveObjectName:
    """Object name with format string bindings that update reactively."""

    def test_name_with_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """name="item-{_id}" updates when variable changes."""

        @decorator
        class TestClass(base_class):
            _id: Variable[int] = new(1)
            _label: QLabel = new("Item", name="item-{_id}")

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        assert_that(instance._label.objectName()).is_equal_to("item-1")

        instance._id.value = 42
        qt.process_events()

        assert_that(instance._label.objectName()).is_equal_to("item-42")

    def test_name_with_record_field_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """name="row-{id}" works with Widget[T] record fields."""
        from dataclasses import dataclass

        @dataclass
        class Row:
            id: int
            text: str

        @decorator(record=Row(5, "Hello"))
        class TestClass(base_class[Row]):
            _label: QLabel = new(bind="{text}", name="row-{id}")

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        assert_that(instance._label.objectName()).is_equal_to("row-5")

        instance.record.id = 99
        qt.process_events()

        assert_that(instance._label.objectName()).is_equal_to("row-99")
