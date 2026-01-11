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

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


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
