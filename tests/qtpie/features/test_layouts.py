# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
"""Tests for layouts across Widget, Window, and App.

Tests vertical, horizontal, form, and grid layouts.
Menu is excluded as it doesn't support layouts.
"""

from typing import Any

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from qtpie import AppBase, Variable, Window, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


def get_layout(instance: Any, base_class: type) -> Any:
    """Get the layout for an instance, handling Window/App differences.

    - Widget: instance.layout()
    - Window: instance.centralWidget().layout()
    - App: instance.window.centralWidget().layout()
    """
    if base_class is Window:
        return instance.centralWidget().layout()
    elif base_class is AppBase:
        return instance.window.centralWidget().layout()
    else:
        return instance.layout()


# =============================================================================
# Vertical Layout (Default)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVerticalLayout:
    """Vertical layout (default or layout='vertical')."""

    def test_default_layout_is_vertical(self, base_class, decorator, qt: QtDriver) -> None:
        """Default layout is QVBoxLayout."""

        @decorator
        class TestClass(base_class):
            label1: QLabel = new("One")
            label2: QLabel = new("Two")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class)).is_instance_of(QVBoxLayout)

    def test_explicit_vertical_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """layout='vertical' creates QVBoxLayout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label1: QLabel = new("One")
            label2: QLabel = new("Two")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class)).is_instance_of(QVBoxLayout)

    def test_vertical_layout_widget_count(self, base_class, decorator, qt: QtDriver) -> None:
        """Vertical layout contains all widgets."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label1: QLabel = new("One")
            label2: QLabel = new("Two")
            label3: QLabel = new("Three")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class).count()).is_equal_to(3)

    def test_vertical_no_label_required(self, base_class, decorator, qt: QtDriver) -> None:
        """Vertical layout doesn't require label= parameter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            name: QLineEdit = new()
            email: QLineEdit = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class).count()).is_equal_to(2)


# =============================================================================
# Horizontal Layout
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestHorizontalLayout:
    """Horizontal layout (layout='horizontal')."""

    def test_horizontal_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """layout='horizontal' creates QHBoxLayout."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            label1: QLabel = new("One")
            label2: QLabel = new("Two")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class)).is_instance_of(QHBoxLayout)

    def test_horizontal_layout_widget_count(self, base_class, decorator, qt: QtDriver) -> None:
        """Horizontal layout contains all widgets."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            btn1: QLabel = new("A")
            btn2: QLabel = new("B")
            btn3: QLabel = new("C")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class).count()).is_equal_to(3)

    def test_horizontal_no_grid_required(self, base_class, decorator, qt: QtDriver) -> None:
        """Horizontal layout doesn't require grid= parameter."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            name: QLineEdit = new()
            submit: QLabel = new("Submit")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class).count()).is_equal_to(2)


# =============================================================================
# Form Layout
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFormLayout:
    """Form layout (layout='form')."""

    def test_form_layout_type(self, base_class, decorator, qt: QtDriver) -> None:
        """layout='form' creates QFormLayout."""

        @decorator(layout="form")
        class TestClass(base_class):
            name: QLineEdit = new(label="Full Name")
            email: QLineEdit = new(label="Email")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class)).is_instance_of(QFormLayout)

    def test_form_layout_row_count(self, base_class, decorator, qt: QtDriver) -> None:
        """Form layout has correct row count."""

        @decorator(layout="form")
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")
            email: QLineEdit = new(label="Email")
            phone: QLineEdit = new(label="Phone")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.rowCount()).is_equal_to(3)

    def test_form_layout_labels(self, base_class, decorator, qt: QtDriver) -> None:
        """Form layout creates labels from label= parameter."""

        @decorator(layout="form")
        class TestClass(base_class):
            name: QLineEdit = new(label="Full Name")
            age: QSpinBox = new(label="Age")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Check first label
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert_that(label_item).is_not_none()
        label_widget = label_item.widget()
        assert_that(label_widget).is_instance_of(QLabel)
        assert_that(label_widget.text()).is_equal_to("Full Name")

    def test_form_layout_requires_label(self, base_class, decorator, qt: QtDriver) -> None:
        """Form layout raises error if label= is missing."""

        @decorator(layout="form")
        class TestClass(base_class):
            name: QLineEdit = new()  # Missing label=

        with pytest.raises(TypeError, match="requires label="):
            create_and_track(qt, TestClass, base_class)

    def test_form_layout_variable_with_label(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in form layout uses label=."""

        @decorator(layout="form")
        class TestClass(base_class):
            _age: Variable[int, QSpinBox] = new(25)(label="Age")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        assert_that(layout).is_instance_of(QFormLayout)
        assert_that(layout.rowCount()).is_equal_to(1)

        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert_that(label_item.widget().text()).is_equal_to("Age")


# =============================================================================
# Grid Layout
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestGridLayout:
    """Grid layout (layout='grid')."""

    def test_grid_layout_type(self, base_class, decorator, qt: QtDriver) -> None:
        """layout='grid' creates QGridLayout."""

        @decorator(layout="grid")
        class TestClass(base_class):
            btn_00: QLabel = new("00", grid=(0, 0))
            btn_01: QLabel = new("01", grid=(0, 1))

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class)).is_instance_of(QGridLayout)

    def test_grid_layout_positioning(self, base_class, decorator, qt: QtDriver) -> None:
        """Grid layout positions widgets correctly."""

        @decorator(layout="grid")
        class TestClass(base_class):
            btn_00: QLabel = new("00", grid=(0, 0))
            btn_01: QLabel = new("01", grid=(0, 1))
            btn_10: QLabel = new("10", grid=(1, 0))
            btn_11: QLabel = new("11", grid=(1, 1))

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        item_00 = layout.itemAtPosition(0, 0)
        assert_that(item_00).is_not_none()
        assert_that(item_00.widget().text()).is_equal_to("00")

        item_01 = layout.itemAtPosition(0, 1)
        assert_that(item_01.widget().text()).is_equal_to("01")

        item_10 = layout.itemAtPosition(1, 0)
        assert_that(item_10.widget().text()).is_equal_to("10")

        item_11 = layout.itemAtPosition(1, 1)
        assert_that(item_11.widget().text()).is_equal_to("11")

    def test_grid_layout_with_span(self, base_class, decorator, qt: QtDriver) -> None:
        """Grid layout supports rowspan and colspan."""

        @decorator(layout="grid")
        class TestClass(base_class):
            # Spans 1 row, 4 cols
            display: QLineEdit = new(grid=(0, 0, 1, 4))
            btn: QLabel = new("X", grid=(1, 0))

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        item = layout.itemAtPosition(0, 0)
        assert_that(item).is_not_none()
        assert_that(item.widget()).is_instance_of(QLineEdit)

        btn_item = layout.itemAtPosition(1, 0)
        assert_that(btn_item.widget().text()).is_equal_to("X")

    def test_grid_layout_requires_grid(self, base_class, decorator, qt: QtDriver) -> None:
        """Grid layout raises error if grid= is missing."""

        @decorator(layout="grid")
        class TestClass(base_class):
            btn: QLabel = new("X")  # Missing grid=

        with pytest.raises(TypeError, match="requires grid="):
            create_and_track(qt, TestClass, base_class)

    def test_grid_layout_variable_with_grid(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in grid layout uses grid=."""

        @decorator(layout="grid")
        class TestClass(base_class):
            _value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))  # type: ignore[type-arg]
            _label: Variable[str, QLabel] = new("Hello")(grid=(0, 1))  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        item_00 = layout.itemAtPosition(0, 0)
        assert_that(item_00.widget()).is_instance_of(QSpinBox)

        item_01 = layout.itemAtPosition(0, 1)
        assert_that(item_01.widget()).is_instance_of(QLabel)


# =============================================================================
# Layout with exclude (layout=False)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLayoutExclusion:
    """Exclude widgets from layout with layout=False."""

    def test_layout_false_excludes_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """layout=False excludes widget from layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            included: QLabel = new("Included")
            excluded: QLabel = new("Excluded", layout=False)

        instance = create_and_track(qt, TestClass, base_class)
        # Only 1 widget in layout (the other is excluded)
        assert_that(get_layout(instance, base_class).count()).is_equal_to(1)

    def test_excluded_widget_still_accessible(self, base_class, decorator, qt: QtDriver) -> None:
        """Excluded widgets are still accessible as attributes."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            included: QLabel = new("A")
            excluded: QLabel = new("B", layout=False)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.included.text()).is_equal_to("A")
        assert_that(instance.excluded.text()).is_equal_to("B")


# =============================================================================
# Mixed Widgets in Layout
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMixedWidgetsInLayout:
    """Various widget types in layouts."""

    def test_mixed_widget_types_vertical(self, base_class, decorator, qt: QtDriver) -> None:
        """Different widget types in vertical layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel = new("Label")
            input_field: QLineEdit = new()
            spinner: QSpinBox = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(get_layout(instance, base_class).count()).is_equal_to(3)

    def test_variable_and_widget_in_form(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] and regular widgets in form layout."""

        @decorator(layout="form")
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")
            _age: Variable[int, QSpinBox] = new(0)(label="Age")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.rowCount()).is_equal_to(2)
