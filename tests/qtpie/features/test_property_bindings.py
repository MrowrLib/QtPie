# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for property bindings (visible=, enabled=) across Widget, Window, and App.

Tests visible= and enabled= reactive bindings with Variables and expressions.
Menu is excluded as it doesn't support QWidget children with these properties.
"""

from dataclasses import dataclass, field
from enum import Enum

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QComboBox, QLabel, QPushButton

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import RECORD_CLASS_TYPES, WIDGET_CLASS_TYPES, create_and_track


# Helper: Qt's isVisible() returns False for hidden parent widgets
# Use isHidden() which checks the widget's own visibility state
def is_widget_visible(widget: QLabel | QPushButton) -> bool:
    """Check if widget's OWN visibility is set to True (ignoring parent visibility)."""
    return not widget.isHidden()


# =============================================================================
# visible= Binding with Variable
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVisibleBindingVariable:
    """visible= bound to a Variable[bool]."""

    def test_visible_binding_initially_true(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with Variable[bool] starting True shows widget."""

        @decorator
        class TestClass(base_class):
            _show: Variable[bool] = new(True)
            label: QLabel = new("Hello", visible="_show")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_true()

    def test_visible_binding_initially_false(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with Variable[bool] starting False hides widget."""

        @decorator
        class TestClass(base_class):
            _show: Variable[bool] = new(False)
            label: QLabel = new("Hidden", visible="_show")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_false()

    def test_visible_updates_on_variable_change(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing Variable value updates widget visibility."""

        @decorator
        class TestClass(base_class):
            _show: Variable[bool] = new(True)
            label: QLabel = new("Toggle", visible="_show")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_true()

        instance._show.value = False
        assert_that(is_widget_visible(instance.label)).is_false()

        instance._show.value = True
        assert_that(is_widget_visible(instance.label)).is_true()

    def test_visible_multiple_toggles(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple visibility toggles work correctly."""

        @decorator
        class TestClass(base_class):
            _show: Variable[bool] = new(False)
            label: QLabel = new("Multi", visible="_show")

        instance = create_and_track(qt, TestClass, base_class)

        for expected in [False, True, False, True, True, False]:
            instance._show.value = expected
            assert_that(is_widget_visible(instance.label)).is_equal_to(expected)


# =============================================================================
# enabled= Binding with Variable
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestEnabledBindingVariable:
    """enabled= bound to a Variable[bool]."""

    def test_enabled_binding_initially_true(self, base_class, decorator, qt: QtDriver) -> None:
        """enabled= with Variable[bool] starting True enables widget."""

        @decorator
        class TestClass(base_class):
            _can_click: Variable[bool] = new(True)
            button: QPushButton = new("Click", enabled="_can_click")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button.isEnabled()).is_true()

    def test_enabled_binding_initially_false(self, base_class, decorator, qt: QtDriver) -> None:
        """enabled= with Variable[bool] starting False disables widget."""

        @decorator
        class TestClass(base_class):
            _can_click: Variable[bool] = new(False)
            button: QPushButton = new("Disabled", enabled="_can_click")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button.isEnabled()).is_false()

    def test_enabled_updates_on_variable_change(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing Variable value updates widget enabled state."""

        @decorator
        class TestClass(base_class):
            _can_click: Variable[bool] = new(True)
            button: QPushButton = new("Toggle", enabled="_can_click")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button.isEnabled()).is_true()

        instance._can_click.value = False
        assert_that(instance.button.isEnabled()).is_false()

        instance._can_click.value = True
        assert_that(instance.button.isEnabled()).is_true()


# =============================================================================
# visible= with Expression Bindings
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVisibleExpressionBinding:
    """visible= with expression bindings."""

    def test_visible_comparison_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with comparison expression like {_count > 0}."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            label: QLabel = new("Has items", visible="{_count > 0}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_false()

        instance._count.value = 1
        assert_that(is_widget_visible(instance.label)).is_true()

        instance._count.value = 0
        assert_that(is_widget_visible(instance.label)).is_false()

    def test_visible_len_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with len() expression."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            label: QLabel = new("Has name", visible="{len(_name) > 0}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_false()

        instance._name.value = "Alice"
        assert_that(is_widget_visible(instance.label)).is_true()

        instance._name.value = ""
        assert_that(is_widget_visible(instance.label)).is_false()

    def test_visible_and_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with boolean 'and' expression."""

        @decorator
        class TestClass(base_class):
            _logged_in: Variable[bool] = new(False)
            _is_admin: Variable[bool] = new(False)
            admin_panel: QLabel = new("Admin", visible="{_logged_in and _is_admin}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.admin_panel)).is_false()

        instance._logged_in.value = True
        assert_that(is_widget_visible(instance.admin_panel)).is_false()

        instance._is_admin.value = True
        assert_that(is_widget_visible(instance.admin_panel)).is_true()

        instance._logged_in.value = False
        assert_that(is_widget_visible(instance.admin_panel)).is_false()

    def test_visible_or_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with boolean 'or' expression."""

        @decorator
        class TestClass(base_class):
            _has_warning: Variable[bool] = new(False)
            _has_error: Variable[bool] = new(False)
            alert: QLabel = new("Alert", visible="{_has_warning or _has_error}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.alert)).is_false()

        instance._has_warning.value = True
        assert_that(is_widget_visible(instance.alert)).is_true()

        instance._has_warning.value = False
        instance._has_error.value = True
        assert_that(is_widget_visible(instance.alert)).is_true()

    def test_visible_not_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with 'not' expression."""

        @decorator
        class TestClass(base_class):
            _loading: Variable[bool] = new(True)
            content: QLabel = new("Content", visible="{not _loading}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.content)).is_false()

        instance._loading.value = False
        assert_that(is_widget_visible(instance.content)).is_true()


# =============================================================================
# enabled= with Expression Bindings
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestEnabledExpressionBinding:
    """enabled= with expression bindings."""

    def test_enabled_len_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """enabled= with len() expression."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.submit.isEnabled()).is_false()

        instance._name.value = "Alice"
        assert_that(instance.submit.isEnabled()).is_true()

        instance._name.value = ""
        assert_that(instance.submit.isEnabled()).is_false()

    def test_enabled_comparison_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """enabled= with comparison expression."""

        @decorator
        class TestClass(base_class):
            _age: Variable[int] = new(0)
            submit: QPushButton = new("Submit", enabled="{_age >= 18}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.submit.isEnabled()).is_false()

        instance._age.value = 18
        assert_that(instance.submit.isEnabled()).is_true()

        instance._age.value = 17
        assert_that(instance.submit.isEnabled()).is_false()

    def test_enabled_equality_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """enabled= with equality expression."""

        @decorator
        class TestClass(base_class):
            _status: Variable[str] = new("pending")
            confirm: QPushButton = new("Confirm", enabled="{_status == 'ready'}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.confirm.isEnabled()).is_false()

        instance._status.value = "ready"
        assert_that(instance.confirm.isEnabled()).is_true()

        instance._status.value = "done"
        assert_that(instance.confirm.isEnabled()).is_false()


# =============================================================================
# Multiple Property Bindings
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMultiplePropertyBindings:
    """Both visible= and enabled= on same widget."""

    def test_both_visible_and_enabled(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget can have both visible= and enabled= bindings."""

        @decorator
        class TestClass(base_class):
            _show: Variable[bool] = new(True)
            _allow: Variable[bool] = new(True)
            button: QPushButton = new("Action", visible="_show", enabled="_allow")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.button)).is_true()
        assert_that(instance.button.isEnabled()).is_true()

        instance._show.value = False
        assert_that(is_widget_visible(instance.button)).is_false()
        assert_that(instance.button.isEnabled()).is_true()

        instance._show.value = True
        instance._allow.value = False
        assert_that(is_widget_visible(instance.button)).is_true()
        assert_that(instance.button.isEnabled()).is_false()

    def test_visible_and_enabled_with_expressions(self, base_class, decorator, qt: QtDriver) -> None:
        """Both properties can use expressions."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            _name: Variable[str] = new("")
            button: QPushButton = new(
                "Submit",
                visible="{_count > 0}",
                enabled="{len(_name) > 0}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.button)).is_false()
        assert_that(instance.button.isEnabled()).is_false()

        instance._count.value = 1
        assert_that(is_widget_visible(instance.button)).is_true()
        assert_that(instance.button.isEnabled()).is_false()

        instance._name.value = "test"
        assert_that(is_widget_visible(instance.button)).is_true()
        assert_that(instance.button.isEnabled()).is_true()


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestPropertyBindingEdgeCases:
    """Edge cases for property bindings."""

    def test_binding_without_underscore(self, base_class, decorator, qt: QtDriver) -> None:
        """Variables without underscore prefix work."""

        @decorator
        class TestClass(base_class):
            show_it: Variable[bool] = new(True)
            label: QLabel = new("Test", visible="show_it")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_true()

        instance.show_it.value = False
        assert_that(is_widget_visible(instance.label)).is_false()

    def test_underscore_lookup_fallback(self, base_class, decorator, qt: QtDriver) -> None:
        """Binding without underscore looks up _name variable."""

        @decorator
        class TestClass(base_class):
            _enabled_flag: Variable[bool] = new(True)
            button: QPushButton = new("Test", enabled="enabled_flag")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button.isEnabled()).is_true()

        instance._enabled_flag.value = False
        assert_that(instance.button.isEnabled()).is_false()

    def test_multiple_widgets_same_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple widgets can bind to same Variable."""

        @decorator
        class TestClass(base_class):
            _show: Variable[bool] = new(True)
            label1: QLabel = new("One", visible="_show")
            label2: QLabel = new("Two", visible="_show")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label1)).is_true()
        assert_that(is_widget_visible(instance.label2)).is_true()

        instance._show.value = False
        assert_that(is_widget_visible(instance.label1)).is_false()
        assert_that(is_widget_visible(instance.label2)).is_false()

    def test_expression_with_multiple_variables(self, base_class, decorator, qt: QtDriver) -> None:
        """Expression using multiple variables reactively updates."""

        @decorator
        class TestClass(base_class):
            _a: Variable[int] = new(0)
            _b: Variable[int] = new(0)
            label: QLabel = new("Sum", visible="{_a + _b > 5}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(is_widget_visible(instance.label)).is_false()

        instance._a.value = 3
        assert_that(is_widget_visible(instance.label)).is_false()

        instance._b.value = 3
        assert_that(is_widget_visible(instance.label)).is_true()

        instance._a.value = 0
        assert_that(is_widget_visible(instance.label)).is_false()


# =============================================================================
# visible= with Record Field (Widget[T]) - Enum expressions
# =============================================================================


class BodyType(Enum):
    """Test enum for body type selection."""

    NONE = "none"
    TEXT = "text"
    JSON = "json"
    XML = "xml"
    FORM_DATA = "form_data"
    FORM_URLENCODED = "form_urlencoded"


@dataclass
class RequestRecord:
    """Test record with enum field."""

    name: str = ""
    body_type: BodyType = BodyType.NONE
    body: str = ""
    body_fields: list[str] = field(default_factory=lambda: [])


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestVisibleWithRecordEnumField:
    """visible= expressions referencing enum fields on Widget[T] records."""

    def test_visible_enum_in_list_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= with enum field 'in' list expression."""

        @decorator(record=RequestRecord(body_type=BodyType.JSON))
        class TestClass(base_class[RequestRecord]):
            label: QLabel = new(
                "Text Editor",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        # JSON is in the list, should be visible
        assert_that(is_widget_visible(instance.label)).is_true()

    def test_visible_enum_not_in_list(self, base_class, decorator, qt: QtDriver) -> None:
        """visible= False when enum value not in list."""

        @decorator(record=RequestRecord(body_type=BodyType.FORM_DATA))
        class TestClass(base_class[RequestRecord]):
            label: QLabel = new(
                "Text Editor",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        # FORM_DATA is NOT in the list, should be hidden
        assert_that(is_widget_visible(instance.label)).is_false()

    def test_visible_enum_updates_reactively(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing record enum field updates visibility."""

        @decorator(record=RequestRecord(body_type=BodyType.TEXT))
        class TestClass(base_class[RequestRecord]):
            text_label: QLabel = new(
                "Text Editor",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )
            form_label: QLabel = new(
                "Form Fields",
                visible="{body_type in [BodyType.FORM_DATA, BodyType.FORM_URLENCODED]}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        # Initially TEXT - text visible, form hidden
        assert_that(is_widget_visible(instance.text_label)).is_true()
        assert_that(is_widget_visible(instance.form_label)).is_false()

        # Change to FORM_DATA - text hidden, form visible
        instance.record.body_type = BodyType.FORM_DATA
        assert_that(is_widget_visible(instance.text_label)).is_false()
        assert_that(is_widget_visible(instance.form_label)).is_true()

        # Change to NONE - both hidden
        instance.record.body_type = BodyType.NONE
        assert_that(is_widget_visible(instance.text_label)).is_false()
        assert_that(is_widget_visible(instance.form_label)).is_false()


class TestVisibleWithWidgetShadowingRecordField:
    """visible= when widget field has same name as record field.

    The expression should use the RECORD field value, not the widget.
    This is a common pattern: QComboBox named 'body_type' binding to record.body_type,
    with visibility expressions like {body_type in [...]}.
    """

    def test_widget_field_shadows_record_field(self, qt: QtDriver) -> None:
        """Widget field with same name as record field uses record value in expression."""

        @widget(record=RequestRecord(body_type=BodyType.JSON))
        class TestWidget(Widget[RequestRecord]):
            # Widget field with SAME NAME as record field
            body_type: QComboBox = new(
                bind=BodyType,
                selectedItem="body_type",
            )
            # Expression uses record.body_type, not the QComboBox widget
            text_editor: QLabel = new(
                "Editor",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )

        instance = qt.track(TestWidget())
        # Record has JSON, which is in the list - should be visible
        assert_that(is_widget_visible(instance.text_editor)).is_true()

        # Change record value - visibility should update
        instance.record.body_type = BodyType.FORM_DATA
        assert_that(is_widget_visible(instance.text_editor)).is_false()

    def test_underscore_widget_field_shadows_record_field(self, qt: QtDriver) -> None:
        """Widget field _body_type doesn't interfere with record.body_type expression."""

        @widget(record=RequestRecord(body_type=BodyType.TEXT))
        class TestWidget(Widget[RequestRecord]):
            _body_type: QComboBox = new(
                bind=BodyType,
                selectedItem="body_type",
            )
            editor: QLabel = new(
                "Editor",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )

        instance = qt.track(TestWidget())
        assert_that(is_widget_visible(instance.editor)).is_true()

        instance.record.body_type = BodyType.NONE
        assert_that(is_widget_visible(instance.editor)).is_false()


class TestVisibleWithDeferredRecordBinding:
    """visible= when record is bound later via bind='record' from parent.

    This tests the timing issue where child Widget[T] creates an empty record,
    then the parent's bind='record' replaces it. The visibility expression
    must re-evaluate after the binding completes.
    """

    def test_child_widget_with_deferred_record_binding(self, qt: QtDriver) -> None:
        """Child widget's visible expression works after bind='record' from parent."""

        @widget
        class ChildWidget(Widget[RequestRecord]):
            editor: QLabel = new(
                "Editor",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )

        @widget(record=RequestRecord(body_type=BodyType.JSON))
        class ParentWidget(Widget[RequestRecord]):
            child: ChildWidget = new(bind="record")

        instance = qt.track(ParentWidget())
        qt.process_events()  # Allow deferred bindings to complete

        # Child should inherit parent's record with body_type=JSON
        assert_that(is_widget_visible(instance.child.editor)).is_true()

        # Changing parent's record should update child's visibility
        instance.record.body_type = BodyType.FORM_DATA
        assert_that(is_widget_visible(instance.child.editor)).is_false()

    def test_nested_child_with_multiple_visible_expressions(self, qt: QtDriver) -> None:
        """Multiple visibility expressions in child widget all work with deferred binding."""

        @widget
        class BodyEditor(Widget[RequestRecord]):
            text_content: QLabel = new(
                "Text",
                visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
            )
            form_fields: QLabel = new(
                "Form",
                visible="{body_type in [BodyType.FORM_DATA, BodyType.FORM_URLENCODED]}",
            )

        @widget(record=RequestRecord(body_type=BodyType.TEXT))
        class RequestEditor(Widget[RequestRecord]):
            body: BodyEditor = new(bind="record")

        instance = qt.track(RequestEditor())
        qt.process_events()

        # TEXT: text visible, form hidden
        assert_that(is_widget_visible(instance.body.text_content)).is_true()
        assert_that(is_widget_visible(instance.body.form_fields)).is_false()

        # FORM_DATA: text hidden, form visible
        instance.record.body_type = BodyType.FORM_DATA
        assert_that(is_widget_visible(instance.body.text_content)).is_false()
        assert_that(is_widget_visible(instance.body.form_fields)).is_true()

        # XML: text visible, form hidden
        instance.record.body_type = BodyType.XML
        assert_that(is_widget_visible(instance.body.text_content)).is_true()
        assert_that(is_widget_visible(instance.body.form_fields)).is_false()


# Models for testing nested optional paths
class AuthType(Enum):
    """Auth type enum for testing."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"


@dataclass
class AuthSettings:
    """Nested auth settings."""

    type: AuthType = AuthType.NONE
    username: str = ""


@dataclass
class RequestWithAuth:
    """Request with optional nested auth."""

    auth: AuthSettings | None = None


class TestVisibleWithNestedOptionalPath:
    """visible= expressions with nested optional paths like auth?.type.

    Regression tests for the bug where visible="{auth?.type == AuthType.BASIC}"
    didn't work because expression.py didn't handle ?. optional chaining.
    """

    def test_visible_nested_optional_path_with_value(self, qt: QtDriver) -> None:
        """visible= with nested optional path when intermediate has value."""

        @widget(record=RequestWithAuth(auth=AuthSettings(type=AuthType.BASIC)))
        class TestWidget(Widget[RequestWithAuth]):
            basic_label: QLabel = new("Basic", visible="{auth?.type == AuthType.BASIC}")
            bearer_label: QLabel = new("Bearer", visible="{auth?.type == AuthType.BEARER}")

        instance = qt.track(TestWidget())

        # auth.type is BASIC - basic visible, bearer hidden
        assert_that(is_widget_visible(instance.basic_label)).is_true()
        assert_that(is_widget_visible(instance.bearer_label)).is_false()

    def test_visible_nested_optional_path_none_intermediate(self, qt: QtDriver) -> None:
        """visible= with nested optional path when intermediate is None."""

        @widget(record=RequestWithAuth(auth=None))
        class TestWidget(Widget[RequestWithAuth]):
            basic_label: QLabel = new("Basic", visible="{auth?.type == AuthType.BASIC}")

        instance = qt.track(TestWidget())

        # auth is None - auth?.type is None, not equal to BASIC
        assert_that(is_widget_visible(instance.basic_label)).is_false()

    def test_visible_nested_optional_path_reactive(self, qt: QtDriver) -> None:
        """visible= with nested optional path updates when value changes."""

        @widget(record=RequestWithAuth(auth=AuthSettings(type=AuthType.BASIC)))
        class TestWidget(Widget[RequestWithAuth]):
            basic_label: QLabel = new("Basic", visible="{auth?.type == AuthType.BASIC}")
            bearer_label: QLabel = new("Bearer", visible="{auth?.type == AuthType.BEARER}")

        instance = qt.track(TestWidget())

        # Initially BASIC
        assert_that(is_widget_visible(instance.basic_label)).is_true()
        assert_that(is_widget_visible(instance.bearer_label)).is_false()

        # Change to BEARER
        instance.record.auth.type = AuthType.BEARER  # type: ignore[union-attr]
        assert_that(is_widget_visible(instance.basic_label)).is_false()
        assert_that(is_widget_visible(instance.bearer_label)).is_true()

    def test_visible_nested_optional_in_list(self, qt: QtDriver) -> None:
        """visible= with nested optional path in list expression."""

        @widget(record=RequestWithAuth(auth=AuthSettings(type=AuthType.BASIC)))
        class TestWidget(Widget[RequestWithAuth]):
            auth_fields: QLabel = new(
                "Auth Fields",
                visible="{auth?.type in [AuthType.BASIC, AuthType.BEARER]}",
            )

        instance = qt.track(TestWidget())

        # BASIC is in list
        assert_that(is_widget_visible(instance.auth_fields)).is_true()

        # Change to NONE (not in list)
        instance.record.auth.type = AuthType.NONE  # type: ignore[union-attr]
        assert_that(is_widget_visible(instance.auth_fields)).is_false()
