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
# pyright: reportUnusedClass=false
"""Tests for layouts across Widget, Window, and App.

Tests vertical, horizontal, form, and grid layouts.
Menu is excluded as it doesn't support layouts.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
)

from qtpie import Stretch, Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track, get_layout

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


# =============================================================================
# Stretch
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestStretch:
    """Stretch adds expandable space to layouts."""

    def test_stretch_default_factor(self, base_class, decorator, qt: QtDriver) -> None:
        """Stretch with no args uses factor=1."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _stretch: Stretch = new()
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: top label, stretch, bottom label
        assert_that(layout.count()).is_equal_to(3)

    def test_stretch_custom_factor(self, base_class, decorator, qt: QtDriver) -> None:
        """Stretch with custom factor."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _stretch: Stretch = new(3)
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)

    def test_stretch_in_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """Stretch works in horizontal layouts."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _stretch: Stretch = new()
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout).is_instance_of(QHBoxLayout)
        assert_that(layout.count()).is_equal_to(3)

    def test_multiple_stretches(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple stretches in one layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _stretch1: Stretch = new()
            middle: QLabel = new("Middle")
            _stretch2: Stretch = new()

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: stretch, label, stretch
        assert_that(layout.count()).is_equal_to(3)


# =============================================================================
# Bare Stretch Annotation
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestBareStretchAnnotation:
    """Bare Stretch annotation (without = new()) is a shorthand for Stretch = new()."""

    def test_bare_stretch_annotation(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare `_stretch: Stretch` works without = new()."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _stretch: Stretch
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: top label, stretch, bottom label
        assert_that(layout.count()).is_equal_to(3)

    def test_multiple_bare_stretch_annotations(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple bare Stretch annotations work."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _stretch1: Stretch
            middle: QLabel = new("Middle")
            _stretch2: Stretch

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: stretch, label, stretch
        assert_that(layout.count()).is_equal_to(3)

    def test_bare_stretch_in_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Stretch works in horizontal layouts."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _stretch: Stretch
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout).is_instance_of(QHBoxLayout)
        assert_that(layout.count()).is_equal_to(3)

    def test_mix_bare_and_new_stretch(self, base_class, decorator, qt: QtDriver) -> None:
        """Mix of bare Stretch and Stretch = new(factor) works."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _stretch1: Stretch  # Bare - default factor 1
            middle: QLabel = new("Middle")
            _stretch2: Stretch = new(3)  # With custom factor

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: stretch, label, stretch
        assert_that(layout.count()).is_equal_to(3)


# =============================================================================
# QSpacerItem
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSpacerItem:
    """QSpacerItem for custom spacing in layouts."""

    def test_spacer_item_basic(self, base_class, decorator, qt: QtDriver) -> None:
        """QSpacerItem with fixed size."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _spacer: QSpacerItem = new(20, 40)
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: top label, spacer, bottom label
        assert_that(layout.count()).is_equal_to(3)

    def test_spacer_item_with_policy(self, base_class, decorator, qt: QtDriver) -> None:
        """QSpacerItem with size policy."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _spacer: QSpacerItem = new(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)

    def test_spacer_item_accessible(self, base_class, decorator, qt: QtDriver) -> None:
        """QSpacerItem is accessible as attribute."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _spacer: QSpacerItem = new(50, 50)
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        # The spacer item is stored on the instance
        assert_that(instance._spacer).is_instance_of(QSpacerItem)


# =============================================================================
# Nested Layouts
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestNestedLayouts:
    """Nested layouts within a widget."""

    def test_nested_layout_basic(self, base_class, decorator, qt: QtDriver) -> None:
        """QHBoxLayout nested in default QVBoxLayout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _row: QHBoxLayout = new()
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: top label, nested layout, bottom label
        assert_that(layout.count()).is_equal_to(3)
        assert_that(instance._row).is_instance_of(QHBoxLayout)

    def test_widget_in_nested_layout_by_string(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget added to nested layout via layout='_row'."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _row: QHBoxLayout = new()
            nested_label: QLabel = new("Nested", layout="_row")
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Main layout has: top, nested_layout, bottom (nested_label is in _row)
        assert_that(layout.count()).is_equal_to(3)

        # Nested layout has the label
        assert_that(instance._row.count()).is_equal_to(1)
        assert_that(instance._row.itemAt(0).widget().text()).is_equal_to("Nested")

    def test_widget_in_nested_layout_by_reference(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget added to nested layout via layout=_row (direct reference)."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _row: QHBoxLayout = new()
            nested_label: QLabel = new("Nested", layout="_row")
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)

        # Nested layout has the label
        assert_that(instance._row.count()).is_equal_to(1)

    def test_multiple_widgets_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple widgets in nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _buttons: QHBoxLayout = new()
            btn1: QLabel = new("OK", layout="_buttons")
            btn2: QLabel = new("Cancel", layout="_buttons")
            footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Main layout: header, buttons_layout, footer
        assert_that(layout.count()).is_equal_to(3)

        # Nested layout: btn1, btn2
        assert_that(instance._buttons.count()).is_equal_to(2)

    def test_stretch_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Stretch can be added to nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _stretch: Stretch = new(layout="_row")
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)

        # Nested layout: left, stretch, right
        assert_that(instance._row.count()).is_equal_to(3)

    def test_spacer_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """QSpacerItem can be added to nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _spacer: QSpacerItem = new(50, 0, layout="_row")
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)

        # Nested layout: left, spacer, right
        assert_that(instance._row.count()).is_equal_to(3)

    def test_nested_layout_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Layout nested within another nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _outer: QHBoxLayout = new()
            _inner: QVBoxLayout = new(layout="_outer")
            inner_label: QLabel = new("Inner", layout="_inner")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Main layout has outer
        assert_that(layout.count()).is_equal_to(1)

        # Outer has inner
        assert_that(instance._outer.count()).is_equal_to(1)

        # Inner has label
        assert_that(instance._inner.count()).is_equal_to(1)

    def test_nested_layout_excluded_from_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested layout with layout=False is not added to default layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            label: QLabel = new("Label")
            _hidden_row: QHBoxLayout = new(layout=False)

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Only the label is in the main layout
        assert_that(layout.count()).is_equal_to(1)
        # But the layout still exists
        assert_that(instance._hidden_row).is_instance_of(QHBoxLayout)

    def test_deeply_nested_layouts(self, base_class, decorator, qt: QtDriver) -> None:
        """Three levels of nested layouts: main > level1 > level2 > level3."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            main_label: QLabel = new("Main")
            _level1: QHBoxLayout = new()
            level1_label: QLabel = new("L1", layout="_level1")
            _level2: QVBoxLayout = new(layout="_level1")
            level2_label: QLabel = new("L2", layout="_level2")
            _level3: QHBoxLayout = new(layout="_level2")
            level3_label: QLabel = new("L3", layout="_level3")
            _level3_stretch: Stretch = new(layout="_level3")
            level3_end: QLabel = new("L3 End", layout="_level3")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Main layout: main_label, _level1
        assert_that(layout.count()).is_equal_to(2)

        # Level 1: level1_label, _level2
        assert_that(instance._level1.count()).is_equal_to(2)

        # Level 2: level2_label, _level3
        assert_that(instance._level2.count()).is_equal_to(2)

        # Level 3: level3_label, stretch, level3_end
        assert_that(instance._level3.count()).is_equal_to(3)

        # Verify the widgets are in the right place
        assert_that(instance._level3.itemAt(0).widget().text()).is_equal_to("L3")
        assert_that(instance._level3.itemAt(2).widget().text()).is_equal_to("L3 End")

    def test_nested_grid_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """QGridLayout nested in main layout with widgets at grid positions."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _grid: QGridLayout = new()
            grid_00: QLabel = new("(0,0)", layout="_grid", grid=(0, 0))
            grid_01: QLabel = new("(0,1)", layout="_grid", grid=(0, 1))
            grid_10: QLabel = new("(1,0)", layout="_grid", grid=(1, 0))
            grid_11: QLabel = new("(1,1)", layout="_grid", grid=(1, 1))
            footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Main layout: header, _grid, footer
        assert_that(layout.count()).is_equal_to(3)

        # Grid layout has 4 widgets
        assert_that(instance._grid.count()).is_equal_to(4)

        # Verify grid positions
        assert_that(instance._grid.itemAtPosition(0, 0).widget().text()).is_equal_to("(0,0)")
        assert_that(instance._grid.itemAtPosition(0, 1).widget().text()).is_equal_to("(0,1)")
        assert_that(instance._grid.itemAtPosition(1, 0).widget().text()).is_equal_to("(1,0)")
        assert_that(instance._grid.itemAtPosition(1, 1).widget().text()).is_equal_to("(1,1)")

    def test_nested_grid_with_span(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested grid layout with rowspan/colspan."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _grid: QGridLayout = new()
            header: QLabel = new("Header spans 2 cols", layout="_grid", grid=(0, 0, 1, 2))
            left: QLabel = new("Left", layout="_grid", grid=(1, 0))
            right: QLabel = new("Right", layout="_grid", grid=(1, 1))

        instance = create_and_track(qt, TestClass, base_class)

        # Grid has 3 widgets
        assert_that(instance._grid.count()).is_equal_to(3)

        # Header at (0,0)
        assert_that(instance._grid.itemAtPosition(0, 0).widget().text()).is_equal_to("Header spans 2 cols")

    def test_nested_form_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """QFormLayout nested in main layout with label= parameter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _form: QFormLayout = new()
            name: QLineEdit = new(layout="_form", label="Name:")
            email: QLineEdit = new(layout="_form", label="Email:")
            footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Main layout: header, _form, footer
        assert_that(layout.count()).is_equal_to(3)

        # Form layout has 2 rows
        assert_that(instance._form.rowCount()).is_equal_to(2)

        # Check labels
        name_label = instance._form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget()
        assert_that(name_label.text()).is_equal_to("Name:")

        email_label = instance._form.itemAt(1, QFormLayout.ItemRole.LabelRole).widget()
        assert_that(email_label.text()).is_equal_to("Email:")

    def test_nested_layout_inside_grid(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested layout inside a grid layout."""

        @decorator(layout="grid")
        class TestClass(base_class):
            corner: QLabel = new("Corner", grid=(0, 0))
            _row: QHBoxLayout = new(grid=(0, 1))
            row_left: QLabel = new("Left", layout="_row")
            row_right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Grid has corner label and nested layout
        assert_that(layout.itemAtPosition(0, 0).widget().text()).is_equal_to("Corner")

        # Nested row has 2 widgets
        assert_that(instance._row.count()).is_equal_to(2)

    def test_nested_grid_requires_grid_for_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget in nested QGridLayout requires grid= parameter."""

        @decorator
        class TestClass(base_class):
            _grid: QGridLayout = new()
            _missing_grid: QLabel = new("Missing", layout="_grid")  # Missing grid=

        with pytest.raises(TypeError, match="requires grid="):
            create_and_track(qt, TestClass, base_class)

    def test_nested_grid_requires_grid_for_nested_layouts(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested layout in nested QGridLayout requires grid= parameter."""

        @decorator
        class TestClass(base_class):
            _grid: QGridLayout = new()
            _row: QHBoxLayout = new(layout="_grid")  # Missing grid=

        with pytest.raises(TypeError, match="requires grid="):
            create_and_track(qt, TestClass, base_class)

    def test_nested_form_requires_label_for_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget in nested QFormLayout requires label= parameter."""

        @decorator
        class TestClass(base_class):
            _form: QFormLayout = new()
            _missing_label: QLineEdit = new(layout="_form")  # Missing label=

        with pytest.raises(TypeError, match="requires label="):
            create_and_track(qt, TestClass, base_class)

    # --- Variable[T, W] in nested layouts ---

    def test_variable_in_nested_hbox(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in nested QHBoxLayout."""

        @decorator
        class TestClass(base_class):
            _row: QHBoxLayout = new()
            _name: Variable[str, QLineEdit] = new("Hello")(layout="_row")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Variable's widget should be in the nested layout
        assert_that(instance._row.count()).is_equal_to(1)
        assert_that(instance._name.value).is_equal_to("Hello")

    def test_variable_in_nested_grid(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in nested QGridLayout with grid= position."""

        @decorator
        class TestClass(base_class):
            _grid: QGridLayout = new()
            _count: Variable[int, QSpinBox] = new(42)(layout="_grid", grid=(0, 0))  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Widget at (0,0)
        item = instance._grid.itemAtPosition(0, 0)
        assert item is not None
        assert_that(item.widget()).is_instance_of(QSpinBox)

    def test_variable_in_nested_form(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in nested QFormLayout with label=."""

        @decorator
        class TestClass(base_class):
            _form: QFormLayout = new()
            _email: Variable[str, QLineEdit] = new("")(layout="_form", label="Email:")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Form should have 1 row with label
        assert_that(instance._form.rowCount()).is_equal_to(1)
        label_item = instance._form.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        assert_that(label_item.widget().text()).is_equal_to("Email:")

    def test_variable_in_nested_grid_requires_grid(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in nested QGridLayout requires grid= parameter."""

        @decorator
        class TestClass(base_class):
            _grid: QGridLayout = new()
            _val: Variable[int, QSpinBox] = new(0)(layout="_grid")  # type: ignore[type-arg]  # Missing grid=

        with pytest.raises(TypeError, match="requires grid="):
            create_and_track(qt, TestClass, base_class)

    def test_variable_in_nested_form_requires_label(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in nested QFormLayout requires label= parameter."""

        @decorator
        class TestClass(base_class):
            _form: QFormLayout = new()
            _val: Variable[str, QLineEdit] = new("")(layout="_form")  # type: ignore[type-arg]  # Missing label=

        with pytest.raises(TypeError, match="requires label="):
            create_and_track(qt, TestClass, base_class)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestNestedLayoutOrdering:
    """Test that nested layouts respect field declaration order."""

    def test_nested_layout_after_widget_preserves_order(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested layout should appear after widgets declared before it."""

        @decorator
        class TestClass(base_class):
            _first: QLabel = new("First")
            _form: QFormLayout = new()
            _last: QLabel = new("Last")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Get items from layout
        items = [layout.itemAt(i).widget() or layout.itemAt(i).layout() for i in range(layout.count())]

        # First label should come before form layout
        first_idx = next(i for i, item in enumerate(items) if isinstance(item, QLabel) and item.text() == "First")
        form_idx = next(i for i, item in enumerate(items) if isinstance(item, QFormLayout))
        last_idx = next(i for i, item in enumerate(items) if isinstance(item, QLabel) and item.text() == "Last")

        assert first_idx < form_idx, "First label should be before form layout"
        assert form_idx < last_idx, "Form layout should be before last label"

    def test_widget_targeting_nested_layout_order(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget targeting nested layout shouldn't affect main layout order."""

        @decorator
        class TestClass(base_class):
            _header: QLabel = new("Header")
            _form: QFormLayout = new()
            _name: QLineEdit = new(layout="_form", label="Name:")
            _footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)

        # Get items from main layout (form has the name field inside)
        items = [layout.itemAt(i).widget() or layout.itemAt(i).layout() for i in range(layout.count())]

        # Find indexes
        header_idx = next(i for i, item in enumerate(items) if isinstance(item, QLabel) and item.text() == "Header")
        form_idx = next(i for i, item in enumerate(items) if isinstance(item, QFormLayout))
        footer_idx = next(i for i, item in enumerate(items) if isinstance(item, QLabel) and item.text() == "Footer")

        assert header_idx < form_idx < footer_idx, "Order should be: Header, Form, Footer"

        # Verify name field is inside form layout
        form = items[form_idx]
        assert form.count() > 0, "Form should have items"


# =============================================================================
# Spacer (fixed pixel spacing)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSpacer:
    """Spacer adds fixed pixel space to layouts via addSpacing()."""

    def test_spacer_with_size(self, base_class, decorator, qt: QtDriver) -> None:
        """Spacer with required size argument."""
        from qtpie import Spacer

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _space: Spacer = new(20)  # 20px fixed space
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: top label, spacer, bottom label
        assert_that(layout.count()).is_equal_to(3)

    def test_spacer_in_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """Spacer works in horizontal layouts."""
        from qtpie import Spacer

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _space: Spacer = new(30)
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout).is_instance_of(QHBoxLayout)
        assert_that(layout.count()).is_equal_to(3)

    def test_spacer_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Spacer can be added to nested layout."""
        from qtpie import Spacer

        @decorator(layout="vertical")
        class TestClass(base_class):
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _space: Spacer = new(10, layout="_row")
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)

        # Nested layout: left, spacer, right
        assert_that(instance._row.count()).is_equal_to(3)

    def test_multiple_spacers(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple spacers in one layout."""
        from qtpie import Spacer

        @decorator(layout="vertical")
        class TestClass(base_class):
            _space1: Spacer = new(10)
            middle: QLabel = new("Middle")
            _space2: Spacer = new(20)

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: spacer, label, spacer
        assert_that(layout.count()).is_equal_to(3)

    def test_spacer_requires_size(self, base_class, decorator, qt: QtDriver) -> None:
        """Spacer without size argument raises error."""
        from qtpie import Spacer

        with pytest.raises(TypeError, match="requires a size argument"):

            @decorator(layout="vertical")
            class TestClass(base_class):
                top: QLabel = new("Top")
                _space: Spacer = new()  # Missing size!
                bottom: QLabel = new("Bottom")


# =============================================================================
# Layout Spacing Configuration
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLayoutSpacing:
    """Test spacing= kwarg for all layout types."""

    def test_vertical_layout_spacing(self, base_class, decorator, qt: QtDriver) -> None:
        """spacing= sets layout.setSpacing() for vertical layout."""

        @decorator(layout="vertical", spacing=15)
        class TestClass(base_class):
            label1: QLabel = new("One")
            label2: QLabel = new("Two")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.spacing()).is_equal_to(15)

    def test_horizontal_layout_spacing(self, base_class, decorator, qt: QtDriver) -> None:
        """spacing= sets layout.setSpacing() for horizontal layout."""

        @decorator(layout="horizontal", spacing=20)
        class TestClass(base_class):
            label1: QLabel = new("One")
            label2: QLabel = new("Two")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.spacing()).is_equal_to(20)

    def test_form_layout_spacing(self, base_class, decorator, qt: QtDriver) -> None:
        """spacing= sets layout.setSpacing() for form layout."""

        @decorator(layout="form", spacing=12)
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")
            email: QLineEdit = new(label="Email")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.spacing()).is_equal_to(12)

    def test_grid_layout_spacing(self, base_class, decorator, qt: QtDriver) -> None:
        """spacing= sets layout.setSpacing() for grid layout."""

        @decorator(layout="grid", spacing=8)
        class TestClass(base_class):
            btn_00: QLabel = new("00", grid=(0, 0))
            btn_01: QLabel = new("01", grid=(0, 1))

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.spacing()).is_equal_to(8)


# =============================================================================
# Grid/Form Horizontal/Vertical Spacing
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLayoutHorizontalVerticalSpacing:
    """Test horizontal_spacing= and vertical_spacing= for grid/form layouts."""

    def test_grid_horizontal_vertical_spacing(self, base_class, decorator, qt: QtDriver) -> None:
        """horizontal_spacing= and vertical_spacing= work for grid layout."""

        @decorator(layout="grid", horizontal_spacing=10, vertical_spacing=20)
        class TestClass(base_class):
            btn_00: QLabel = new("00", grid=(0, 0))
            btn_01: QLabel = new("01", grid=(0, 1))
            btn_10: QLabel = new("10", grid=(1, 0))
            btn_11: QLabel = new("11", grid=(1, 1))

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.horizontalSpacing()).is_equal_to(10)
        assert_that(layout.verticalSpacing()).is_equal_to(20)

    def test_form_horizontal_vertical_spacing(self, base_class, decorator, qt: QtDriver) -> None:
        """horizontal_spacing= and vertical_spacing= work for form layout."""

        @decorator(layout="form", horizontal_spacing=15, vertical_spacing=25)
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")
            email: QLineEdit = new(label="Email")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.horizontalSpacing()).is_equal_to(15)
        assert_that(layout.verticalSpacing()).is_equal_to(25)


# =============================================================================
# Form Layout Configuration
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFormLayoutConfig:
    """Test form-specific layout configuration kwargs."""

    def test_form_row_wrap_policy(self, base_class, decorator, qt: QtDriver) -> None:
        """row_wrap_policy= sets QFormLayout.setRowWrapPolicy()."""

        @decorator(layout="form", row_wrap_policy="wrap_all")
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.rowWrapPolicy()).is_equal_to(QFormLayout.RowWrapPolicy.WrapAllRows)

    def test_form_field_growth_policy(self, base_class, decorator, qt: QtDriver) -> None:
        """field_growth_policy= sets QFormLayout.setFieldGrowthPolicy()."""

        @decorator(layout="form", field_growth_policy="expanding_fields_grow")
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.fieldGrowthPolicy()).is_equal_to(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    def test_form_label_alignment(self, base_class, decorator, qt: QtDriver) -> None:
        """label_alignment= sets QFormLayout.setLabelAlignment()."""
        from qtpy.QtCore import Qt

        @decorator(layout="form", label_alignment=Qt.AlignmentFlag.AlignRight)
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.labelAlignment()).is_equal_to(Qt.AlignmentFlag.AlignRight)

    def test_form_alignment(self, base_class, decorator, qt: QtDriver) -> None:
        """form_alignment= sets QFormLayout.setFormAlignment()."""
        from qtpy.QtCore import Qt

        @decorator(layout="form", form_alignment=Qt.AlignmentFlag.AlignHCenter)
        class TestClass(base_class):
            name: QLineEdit = new(label="Name")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.formAlignment()).is_equal_to(Qt.AlignmentFlag.AlignHCenter)


# =============================================================================
# Size Constraint
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSizeConstraint:
    """Test size_constraint= kwarg for all layout types."""

    def test_size_constraint_fixed(self, base_class, decorator, qt: QtDriver) -> None:
        """size_constraint='fixed' sets SetFixedSize constraint."""
        from PySide6.QtWidgets import QLayout

        @decorator(layout="vertical", size_constraint="fixed")
        class TestClass(base_class):
            label: QLabel = new("Label")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.sizeConstraint()).is_equal_to(QLayout.SizeConstraint.SetFixedSize)

    def test_size_constraint_minimum(self, base_class, decorator, qt: QtDriver) -> None:
        """size_constraint='minimum' sets SetMinimumSize constraint."""
        from PySide6.QtWidgets import QLayout

        @decorator(layout="horizontal", size_constraint="minimum")
        class TestClass(base_class):
            label: QLabel = new("Label")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.sizeConstraint()).is_equal_to(QLayout.SizeConstraint.SetMinimumSize)

    def test_size_constraint_maximum(self, base_class, decorator, qt: QtDriver) -> None:
        """size_constraint='maximum' sets SetMaximumSize constraint."""
        from PySide6.QtWidgets import QLayout

        @decorator(layout="vertical", size_constraint="maximum")
        class TestClass(base_class):
            label: QLabel = new("Label")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.sizeConstraint()).is_equal_to(QLayout.SizeConstraint.SetMaximumSize)

    def test_size_constraint_no_constraint(self, base_class, decorator, qt: QtDriver) -> None:
        """size_constraint='no_constraint' sets SetNoConstraint."""
        from PySide6.QtWidgets import QLayout

        @decorator(layout="vertical", size_constraint="no_constraint")
        class TestClass(base_class):
            label: QLabel = new("Label")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.sizeConstraint()).is_equal_to(QLayout.SizeConstraint.SetNoConstraint)
