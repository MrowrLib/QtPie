# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for widget attributes on @widget decorator.

Tests attributes= and styledBackground= parameters on decorators.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import Qt

from qtpie.testing import QtDriver

from .conftest import QWIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# styledBackground= shorthand
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestStyledBackgroundShorthand:
    """@decorator(styledBackground=True) sets WA_StyledBackground attribute."""

    def test_styled_background_true(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(styledBackground=True) sets WA_StyledBackground."""

        @decorator(styledBackground=True)
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()

    def test_styled_background_false_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """By default, WA_StyledBackground is not set."""

        @decorator
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_false()

    def test_styled_background_explicit_false(self, base_class, decorator, qt: QtDriver) -> None:
        """@decorator(styledBackground=False) does not set WA_StyledBackground."""

        @decorator(styledBackground=False)
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_false()


# =============================================================================
# attributes= dict
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestAttributesDict:
    """@decorator(attributes={...}) sets widget attributes."""

    def test_attributes_dict_single_true(self, base_class, decorator, qt: QtDriver) -> None:
        """attributes={WA_StyledBackground: True} sets the attribute."""

        @decorator(attributes={Qt.WidgetAttribute.WA_StyledBackground: True})
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()

    def test_attributes_dict_single_false(self, base_class, decorator, qt: QtDriver) -> None:
        """attributes={WA_StyledBackground: False} clears the attribute."""

        @decorator(attributes={Qt.WidgetAttribute.WA_StyledBackground: False})
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_false()

    def test_attributes_dict_multiple(self, base_class, decorator, qt: QtDriver) -> None:
        """attributes={...} can set multiple attributes."""

        @decorator(
            attributes={
                Qt.WidgetAttribute.WA_StyledBackground: True,
                Qt.WidgetAttribute.WA_TranslucentBackground: True,
            }
        )
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)).is_true()

    def test_attributes_dict_mixed_values(self, base_class, decorator, qt: QtDriver) -> None:
        """attributes={...} can mix True and False values."""

        @decorator(
            attributes={
                Qt.WidgetAttribute.WA_StyledBackground: True,
                Qt.WidgetAttribute.WA_NoSystemBackground: False,
            }
        )
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)).is_false()


# =============================================================================
# attributes= tuple
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestAttributesTuple:
    """@decorator(attributes=(...)) sets all attributes to True."""

    def test_attributes_tuple_single(self, base_class, decorator, qt: QtDriver) -> None:
        """attributes=(WA_StyledBackground,) sets the attribute to True."""

        @decorator(attributes=(Qt.WidgetAttribute.WA_StyledBackground,))
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()

    def test_attributes_tuple_multiple(self, base_class, decorator, qt: QtDriver) -> None:
        """attributes=(...) with multiple attributes sets all to True."""

        @decorator(
            attributes=(
                Qt.WidgetAttribute.WA_StyledBackground,
                Qt.WidgetAttribute.WA_TranslucentBackground,
            )
        )
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)).is_true()


# =============================================================================
# Combined attributes= and styledBackground=
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestCombinedAttributesAndStyledBackground:
    """Using both attributes= and styledBackground= together."""

    def test_styled_background_with_other_attributes(self, base_class, decorator, qt: QtDriver) -> None:
        """styledBackground=True can be combined with attributes=."""

        @decorator(
            styledBackground=True,
            attributes={Qt.WidgetAttribute.WA_TranslucentBackground: True},
        )
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)).is_true()

    def test_styled_background_overrides_attributes(self, base_class, decorator, qt: QtDriver) -> None:
        """styledBackground=True overrides attributes={WA_StyledBackground: False}."""

        @decorator(
            styledBackground=True,
            attributes={Qt.WidgetAttribute.WA_StyledBackground: False},
        )
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        # styledBackground=True is applied after attributes dict, so it wins
        assert_that(instance.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)).is_true()
