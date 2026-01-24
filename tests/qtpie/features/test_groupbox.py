# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
"""QGroupBox support with group= parameter."""

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QGroupBox, QLabel, QLineEdit, QVBoxLayout

from qtpie import Variable, WidgetRepeater, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track, get_layout


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestGroupBox:
    """QGroupBox support with group= parameter."""

    def test_groupbox_basic(self, base_class, decorator, qt: QtDriver) -> None:
        """QGroupBox with widgets added via group= string."""

        @decorator
        class TestClass(base_class):
            _group: QGroupBox = new("The Cool Group Box")
            label1: QLabel = new("Label 1", group="_group")
            label2: QLabel = new("Label 2", group="_group")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._group).is_instance_of(QGroupBox)
        assert_that(instance._group.title()).is_equal_to("The Cool Group Box")
        # Group box should have a layout with 2 widgets
        group_layout = instance._group.layout()
        assert_that(group_layout).is_not_none()
        assert_that(group_layout.count()).is_equal_to(2)

    def test_groupbox_in_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """QGroupBox is added to the parent layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _group: QGroupBox = new("Settings")
            setting1: QLabel = new("Setting 1", group="_group")
            setting2: QLabel = new("Setting 2", group="_group")

        instance = create_and_track(qt, TestClass, base_class)

        # Group box should be in main layout
        # header + group = 2 items in layout
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)
        # First item is header, second is group box
        assert_that(layout.itemAt(0).widget()).is_same_as(instance.header)
        assert_that(layout.itemAt(1).widget()).is_same_as(instance._group)

    def test_groupbox_excludes_from_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets with group= are not added to the default layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _group: QGroupBox = new("Options")
            option1: QLabel = new("Option 1", group="_group")
            option2: QLabel = new("Option 2", group="_group")
            footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout: header, group, footer (3 items)
        # NOT: header, group, option1, option2, footer (5 items)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance.header)
        assert_that(layout.itemAt(1).widget()).is_same_as(instance._group)
        assert_that(layout.itemAt(2).widget()).is_same_as(instance.footer)

        # Group box contains option1 and option2
        group_layout = instance._group.layout()
        assert_that(group_layout.count()).is_equal_to(2)

    def test_multiple_groupboxes(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple group boxes in the same widget."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _general_group: QGroupBox = new("General")
            name: QLabel = new("Name", group="_general_group")
            email: QLabel = new("Email", group="_general_group")

            _advanced_group: QGroupBox = new("Advanced")
            debug: QLabel = new("Debug", group="_advanced_group")
            verbose: QLabel = new("Verbose", group="_advanced_group")

        instance = create_and_track(qt, TestClass, base_class)

        # Layout has 2 group boxes
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)

        # Each group box has 2 widgets
        assert_that(instance._general_group.layout().count()).is_equal_to(2)
        assert_that(instance._advanced_group.layout().count()).is_equal_to(2)

        assert_that(instance._general_group.title()).is_equal_to("General")
        assert_that(instance._advanced_group.title()).is_equal_to("Advanced")

    def test_nested_groupboxes(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested group boxes - a group box inside another group box."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _outer: QGroupBox = new("Outer Group")
            outer_label: QLabel = new("Outer Label", group="_outer")
            _inner: QGroupBox = new("Inner Group", group="_outer")
            inner_label: QLabel = new("Inner Label", group="_inner")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the outer group
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance._outer)

        # Outer group contains: outer_label + inner group
        outer_layout = instance._outer.layout()
        assert_that(outer_layout.count()).is_equal_to(2)

        # Inner group contains: inner_label
        inner_layout = instance._inner.layout()
        assert_that(inner_layout.count()).is_equal_to(1)

        assert_that(instance._outer.title()).is_equal_to("Outer Group")
        assert_that(instance._inner.title()).is_equal_to("Inner Group")

    def test_groupbox_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Group box placed inside a nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            # Top-level group box (goes into main layout)
            _top_group: QGroupBox = new("Top Group")
            top_label: QLabel = new("Top Label", group="_top_group")

            # Nested layout (goes into main layout)
            _nested_layout: QVBoxLayout

            # Group box inside the nested layout
            _nested_group: QGroupBox = new("Nested Group", layout="_nested_layout")
            nested_label: QLabel = new("Nested Label", group="_nested_group")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has: top_group + nested_layout
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance._top_group)
        # Second item is the nested layout
        assert_that(layout.itemAt(1).layout()).is_same_as(instance._nested_layout)

        # Top group contains its label
        top_group_layout = instance._top_group.layout()
        assert_that(top_group_layout.count()).is_equal_to(1)

        # Nested layout contains the nested group
        assert_that(instance._nested_layout.count()).is_equal_to(1)
        assert_that(instance._nested_layout.itemAt(0).widget()).is_same_as(instance._nested_group)

        # Nested group contains its label
        nested_group_layout = instance._nested_group.layout()
        assert_that(nested_group_layout.count()).is_equal_to(1)

    def test_variable_widget_in_groupbox(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] with group= places the widget in the group box."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _group: QGroupBox = new("Input Group")
            _name: Variable[str, QLineEdit] = new("default")(group="_group", placeholderText="Name")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the group box
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Group box contains the QLineEdit
        group_layout = instance._group.layout()
        assert_that(group_layout.count()).is_equal_to(1)
        assert_that(group_layout.itemAt(0).widget()).is_same_as(instance._name.widget)

        # Widget kwargs were applied
        assert_that(instance._name.widget.placeholderText()).is_equal_to("Name")

    def test_list_widget_repeater_in_groupbox(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QWidget] = new(bind=..., group=...) places repeater in group box."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            _group: QGroupBox = new("Items Group")
            _labels: list[QLabel] = new(bind="_items", group="_group")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the group box
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Group box contains the repeater (1 widget)
        group_layout = instance._group.layout()
        assert_that(group_layout.count()).is_equal_to(1)

        # Repeater contains 3 labels
        assert_that(instance._labels.widget_count()).is_equal_to(3)

    def test_variable_list_repeater_in_groupbox(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[T], W] with group= places repeater in group box."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _group: QGroupBox = new("List Group")
            _items: Variable[list[str], QLabel] = new(["x", "y"])(group="_group")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the group box
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Group box contains the repeater (1 widget)
        group_layout = instance._group.layout()
        assert_that(group_layout.count()).is_equal_to(1)

        # Repeater contains 2 labels
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_variable_dict_repeater_in_groupbox(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[K,V]] + list[W] with group= places repeater in group box."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
            _group: QGroupBox = new("Scores Group")
            _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", group="_group")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the group box
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Group box contains the repeater (1 widget)
        group_layout = instance._group.layout()
        assert_that(group_layout.count()).is_equal_to(1)

        # Repeater contains 2 labels
        assert_that(instance._labels.widget_count()).is_equal_to(2)
