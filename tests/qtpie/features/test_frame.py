# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
"""QFrame support with group= parameter."""

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QVBoxLayout

from qtpie import Variable, WidgetRepeater, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track, get_layout


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFrame:
    """QFrame support with group= parameter."""

    def test_frame_basic(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with widgets added via group= string."""

        @decorator
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Box)
            label1: QLabel = new("Label 1", group="_frame")
            label2: QLabel = new("Label 2", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._frame).is_instance_of(QFrame)
        assert_that(instance._frame.frameShape()).is_equal_to(QFrame.Shape.Box)
        # Frame should have a layout with 2 widgets
        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_not_none()
        assert_that(frame_layout.count()).is_equal_to(2)

    def test_frame_with_shadow(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with frameShape and frameShadow."""

        @decorator
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Panel, frameShadow=QFrame.Shadow.Sunken)
            label: QLabel = new("Content", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._frame.frameShape()).is_equal_to(QFrame.Shape.Panel)
        assert_that(instance._frame.frameShadow()).is_equal_to(QFrame.Shadow.Sunken)

    def test_frame_in_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame is added to the parent layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _frame: QFrame = new(frameShape=QFrame.Shape.StyledPanel)
            setting1: QLabel = new("Setting 1", group="_frame")
            setting2: QLabel = new("Setting 2", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        # Frame should be in main layout
        # header + frame = 2 items in layout
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)
        # First item is header, second is frame
        assert_that(layout.itemAt(0).widget()).is_same_as(instance.header)
        assert_that(layout.itemAt(1).widget()).is_same_as(instance._frame)

    def test_frame_excludes_from_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets with group= are not added to the default layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _frame: QFrame = new(frameShape=QFrame.Shape.Box)
            option1: QLabel = new("Option 1", group="_frame")
            option2: QLabel = new("Option 2", group="_frame")
            footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout: header, frame, footer (3 items)
        # NOT: header, frame, option1, option2, footer (5 items)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance.header)
        assert_that(layout.itemAt(1).widget()).is_same_as(instance._frame)
        assert_that(layout.itemAt(2).widget()).is_same_as(instance.footer)

        # Frame contains option1 and option2
        frame_layout = instance._frame.layout()
        assert_that(frame_layout.count()).is_equal_to(2)

    def test_multiple_frames(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple frames in the same widget."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _general_frame: QFrame = new(frameShape=QFrame.Shape.Box)
            name: QLabel = new("Name", group="_general_frame")
            email: QLabel = new("Email", group="_general_frame")

            _advanced_frame: QFrame = new(frameShape=QFrame.Shape.Panel, frameShadow=QFrame.Shadow.Raised)
            debug: QLabel = new("Debug", group="_advanced_frame")
            verbose: QLabel = new("Verbose", group="_advanced_frame")

        instance = create_and_track(qt, TestClass, base_class)

        # Layout has 2 frames
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)

        # Each frame has 2 widgets
        assert_that(instance._general_frame.layout().count()).is_equal_to(2)
        assert_that(instance._advanced_frame.layout().count()).is_equal_to(2)

        assert_that(instance._general_frame.frameShape()).is_equal_to(QFrame.Shape.Box)
        assert_that(instance._advanced_frame.frameShape()).is_equal_to(QFrame.Shape.Panel)
        assert_that(instance._advanced_frame.frameShadow()).is_equal_to(QFrame.Shadow.Raised)

    def test_nested_frames(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested frames - a frame inside another frame."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _outer: QFrame = new(frameShape=QFrame.Shape.Box)
            outer_label: QLabel = new("Outer Label", group="_outer")
            _inner: QFrame = new(frameShape=QFrame.Shape.Panel, group="_outer")
            inner_label: QLabel = new("Inner Label", group="_inner")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the outer frame
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance._outer)

        # Outer frame contains: outer_label + inner frame
        outer_layout = instance._outer.layout()
        assert_that(outer_layout.count()).is_equal_to(2)

        # Inner frame contains: inner_label
        inner_layout = instance._inner.layout()
        assert_that(inner_layout.count()).is_equal_to(1)

        assert_that(instance._outer.frameShape()).is_equal_to(QFrame.Shape.Box)
        assert_that(instance._inner.frameShape()).is_equal_to(QFrame.Shape.Panel)

    def test_frame_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Frame placed inside a nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            # Top-level frame (goes into main layout)
            _top_frame: QFrame = new(frameShape=QFrame.Shape.Box)
            top_label: QLabel = new("Top Label", group="_top_frame")

            # Nested layout (goes into main layout)
            _nested_layout: QVBoxLayout

            # Frame inside the nested layout
            _nested_frame: QFrame = new(frameShape=QFrame.Shape.Panel, layout="_nested_layout")
            nested_label: QLabel = new("Nested Label", group="_nested_frame")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has: top_frame + nested_layout
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance._top_frame)
        # Second item is the nested layout
        assert_that(layout.itemAt(1).layout()).is_same_as(instance._nested_layout)

        # Top frame contains its label
        top_frame_layout = instance._top_frame.layout()
        assert_that(top_frame_layout.count()).is_equal_to(1)

        # Nested layout contains the nested frame
        assert_that(instance._nested_layout.count()).is_equal_to(1)
        assert_that(instance._nested_layout.itemAt(0).widget()).is_same_as(instance._nested_frame)

        # Nested frame contains its label
        nested_frame_layout = instance._nested_frame.layout()
        assert_that(nested_frame_layout.count()).is_equal_to(1)

    def test_variable_widget_in_frame(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] with group= places the widget in the frame."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.StyledPanel)
            _name: Variable[str, QLineEdit] = new("default")(group="_frame", placeholderText="Name")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the frame
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Frame contains the QLineEdit
        frame_layout = instance._frame.layout()
        assert_that(frame_layout.count()).is_equal_to(1)
        assert_that(frame_layout.itemAt(0).widget()).is_same_as(instance._name.widget)

        # Widget kwargs were applied
        assert_that(instance._name.widget.placeholderText()).is_equal_to("Name")

    def test_list_widget_repeater_in_frame(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QWidget] = new(bind=..., group=...) places repeater in frame."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            _frame: QFrame = new(frameShape=QFrame.Shape.Box)
            _labels: list[QLabel] = new(bind="_items", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the frame
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Frame contains the repeater (1 widget)
        frame_layout = instance._frame.layout()
        assert_that(frame_layout.count()).is_equal_to(1)

        # Repeater contains 3 labels
        assert_that(instance._labels.widget_count()).is_equal_to(3)

    def test_variable_list_repeater_in_frame(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[T], W] with group= places repeater in frame."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Panel)
            _items: Variable[list[str], QLabel] = new(["x", "y"])(group="_frame")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the frame
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Frame contains the repeater (1 widget)
        frame_layout = instance._frame.layout()
        assert_that(frame_layout.count()).is_equal_to(1)

        # Repeater contains 2 labels
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_variable_dict_repeater_in_frame(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[K,V]] + list[W] with group= places repeater in frame."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
            _frame: QFrame = new(frameShape=QFrame.Shape.StyledPanel)
            _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the frame
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Frame contains the repeater (1 widget)
        frame_layout = instance._frame.layout()
        assert_that(frame_layout.count()).is_equal_to(1)

        # Repeater contains 2 labels
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_frame_inner_layout_vertical(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with explicit inner_layout='vertical'."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Box, inner_layout="vertical")
            label1: QLabel = new("Label 1", group="_frame")
            label2: QLabel = new("Label 2", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_instance_of(QVBoxLayout)
        assert_that(frame_layout.count()).is_equal_to(2)

    def test_frame_inner_layout_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with inner_layout='horizontal'."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Box, inner_layout="horizontal")
            label1: QLabel = new("Label 1", group="_frame")
            label2: QLabel = new("Label 2", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_instance_of(QHBoxLayout)
        assert_that(frame_layout.count()).is_equal_to(2)

    def test_frame_inner_layout_form(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with inner_layout='form' and label= on children."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.StyledPanel, inner_layout="form")
            name: QLineEdit = new(group="_frame", label="Name:")
            email: QLineEdit = new(group="_frame", label="Email:")

        instance = create_and_track(qt, TestClass, base_class)

        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_instance_of(QFormLayout)
        assert_that(frame_layout.rowCount()).is_equal_to(2)

        # Check labels were created
        name_label = frame_layout.itemAt(0, QFormLayout.ItemRole.LabelRole).widget()
        assert_that(name_label.text()).is_equal_to("Name:")

        email_label = frame_layout.itemAt(1, QFormLayout.ItemRole.LabelRole).widget()
        assert_that(email_label.text()).is_equal_to("Email:")

    def test_frame_inner_layout_grid(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with inner_layout='grid' and grid= on children."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Panel, inner_layout="grid")
            btn_00: QLabel = new("(0,0)", group="_frame", grid=(0, 0))
            btn_01: QLabel = new("(0,1)", group="_frame", grid=(0, 1))
            btn_10: QLabel = new("(1,0)", group="_frame", grid=(1, 0))
            btn_11: QLabel = new("(1,1)", group="_frame", grid=(1, 1))

        instance = create_and_track(qt, TestClass, base_class)

        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_instance_of(QGridLayout)
        assert_that(frame_layout.count()).is_equal_to(4)

        # Check grid positions
        assert_that(frame_layout.itemAtPosition(0, 0).widget().text()).is_equal_to("(0,0)")
        assert_that(frame_layout.itemAtPosition(0, 1).widget().text()).is_equal_to("(0,1)")
        assert_that(frame_layout.itemAtPosition(1, 0).widget().text()).is_equal_to("(1,0)")
        assert_that(frame_layout.itemAtPosition(1, 1).widget().text()).is_equal_to("(1,1)")

    def test_frame_inner_layout_form_with_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in form-layout frame with label=."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Box, inner_layout="form")
            _age: Variable[int, QSpinBox] = new(25)(group="_frame", label="Age:")

        instance = create_and_track(qt, TestClass, base_class)

        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_instance_of(QFormLayout)
        assert_that(frame_layout.rowCount()).is_equal_to(1)

        # Check label
        age_label = frame_layout.itemAt(0, QFormLayout.ItemRole.LabelRole).widget()
        assert_that(age_label.text()).is_equal_to("Age:")

    def test_frame_inner_layout_grid_with_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] in grid-layout frame with grid=."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.StyledPanel, inner_layout="grid")
            _value: Variable[int, QSpinBox] = new(10)(group="_frame", grid=(0, 0))
            _label: Variable[str, QLabel] = new("Hello")(group="_frame", grid=(0, 1))

        instance = create_and_track(qt, TestClass, base_class)

        frame_layout = instance._frame.layout()
        assert_that(frame_layout).is_instance_of(QGridLayout)

        item_00 = frame_layout.itemAtPosition(0, 0)
        assert_that(item_00.widget()).is_instance_of(QSpinBox)

        item_01 = frame_layout.itemAtPosition(0, 1)
        assert_that(item_01.widget()).is_instance_of(QLabel)

    def test_frame_no_shape(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with no explicit shape (NoFrame default)."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new()
            label: QLabel = new("Content", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._frame).is_instance_of(QFrame)
        # Default shape is NoFrame
        assert_that(instance._frame.frameShape()).is_equal_to(QFrame.Shape.NoFrame)
        frame_layout = instance._frame.layout()
        assert_that(frame_layout.count()).is_equal_to(1)

    def test_frame_line_width(self, base_class, decorator, qt: QtDriver) -> None:
        """QFrame with custom lineWidth."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _frame: QFrame = new(frameShape=QFrame.Shape.Box, lineWidth=3)
            label: QLabel = new("Content", group="_frame")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._frame.lineWidth()).is_equal_to(3)
