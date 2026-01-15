# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
"""Tests for auto-new() bare type annotations.

This feature allows bare type annotations to auto-instantiate:
    _label: QLabel           # Auto: creates QLabel()
    _label: QLabel = new()   # Explicit: also creates QLabel()
    _label: QLabel = none()  # Opt-out: no instance created
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from qtpie import Variable, new, none
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# Basic Auto-New
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestAutoNew:
    """Bare type annotations auto-instantiate."""

    def test_bare_qlabel_auto_instantiates(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare QLabel annotation creates QLabel()."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.label).is_instance_of(QLabel)

    def test_bare_qpushbutton_auto_instantiates(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare QPushButton annotation creates QPushButton()."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            button: QPushButton

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button).is_instance_of(QPushButton)

    def test_multiple_bare_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple bare annotations all instantiate."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel
            button: QPushButton
            input: QLineEdit

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.label).is_instance_of(QLabel)
        assert_that(instance.button).is_instance_of(QPushButton)
        assert_that(instance.input).is_instance_of(QLineEdit)


# =============================================================================
# Explicit new() Still Works
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestExplicitNewStillWorks:
    """Explicit = new() still works as before."""

    def test_explicit_new_with_no_args(self, base_class, decorator, qt: QtDriver) -> None:
        """= new() with no args creates instance."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.label).is_instance_of(QLabel)

    def test_explicit_new_with_args(self, base_class, decorator, qt: QtDriver) -> None:
        """= new("text") passes args to constructor."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel = new("Hello World")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.label).is_instance_of(QLabel)
        assert_that(instance.label.text()).is_equal_to("Hello World")


# =============================================================================
# Opt-out with none()
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestNoneOptOut:
    """= none() opts out of auto-instantiation."""

    def test_none_prevents_instantiation(self, base_class, decorator, qt: QtDriver) -> None:
        """= none() means no instance is created."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            placeholder: QLabel = none()

        instance = create_and_track(qt, TestClass, base_class)
        # Should NOT have the attribute or it should be the sentinel
        assert_that(hasattr(instance, "placeholder")).is_false()

    def test_mix_bare_and_none(self, base_class, decorator, qt: QtDriver) -> None:
        """Mix of bare annotations and none() works."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel  # Auto-instantiate
            placeholder: QLabel = none()  # Skip
            button: QPushButton  # Auto-instantiate

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.label).is_instance_of(QLabel)
        assert_that(instance.button).is_instance_of(QPushButton)
        assert_that(hasattr(instance, "placeholder")).is_false()


# =============================================================================
# Variables Are Unaffected
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVariablesUnaffected:
    """Variable[T] types are not affected by auto-new."""

    def test_explicit_variable_still_works(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable with = new() still works."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            count: Variable[int] = new(42)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.count.value).is_equal_to(42)

    def test_bare_variable_is_required_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[T] remains a required binding (not auto-newed)."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            count: Variable[int]  # Bare - should be required binding

        # Required bindings should be in config
        config = TestClass._qtpie_config
        assert_that("count" in config.required_bindings).is_true()


# =============================================================================
# Mix of All Patterns
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMixedPatterns:
    """All patterns work together in the same class."""

    def test_mix_of_all_patterns(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare, explicit, none(), and Variable all work together."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            bare_label: QLabel  # Auto-new
            explicit_label: QLabel = new("Explicit")  # Explicit
            skipped: QLabel = none()  # Opt-out
            count: Variable[int] = new(100)  # Variable

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.bare_label).is_instance_of(QLabel)
        assert_that(instance.explicit_label.text()).is_equal_to("Explicit")
        assert_that(hasattr(instance, "skipped")).is_false()
        assert_that(instance.count.value).is_equal_to(100)
