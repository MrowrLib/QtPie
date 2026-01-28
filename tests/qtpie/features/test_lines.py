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
"""Tests for HorizontalLine, VerticalLine, and Line layout helpers.

These are shorthand for QFrame with HLine/VLine frameShape.
Line auto-selects based on layout orientation.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from qtpie import HorizontalLine, Line, VerticalLine, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track, get_layout

# =============================================================================
# HorizontalLine
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestHorizontalLine:
    """HorizontalLine adds a horizontal divider (QFrame with HLine)."""

    def test_bare_horizontal_line(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare `_line: HorizontalLine` creates HLine QFrame."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _line: HorizontalLine
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: top label, line, bottom label
        assert_that(layout.count()).is_equal_to(3)

        # The middle item should be a QFrame with HLine shape
        line_item = layout.itemAt(1)
        assert_that(line_item).is_not_none()
        line_widget = line_item.widget()
        assert_that(line_widget).is_instance_of(QFrame)
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_horizontal_line_with_new(self, base_class, decorator, qt: QtDriver) -> None:
        """HorizontalLine = new() also works."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _line: HorizontalLine = new()
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)

        line_widget = layout.itemAt(1).widget()
        assert_that(line_widget).is_instance_of(QFrame)
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_horizontal_line_in_horizontal_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """HorizontalLine in horizontal layout still has HLine shape."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _line: HorizontalLine
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout).is_instance_of(QHBoxLayout)
        assert_that(layout.count()).is_equal_to(3)

        line_widget = layout.itemAt(1).widget()
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_horizontal_line_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """HorizontalLine can target a nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _row: QVBoxLayout = new()
            top: QLabel = new("Top", layout="_row")
            _line: HorizontalLine = new(layout="_row")
            bottom: QLabel = new("Bottom", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)
        # Nested layout should have 3 items
        assert_that(instance._row.count()).is_equal_to(3)

        line_widget = instance._row.itemAt(1).widget()
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_multiple_horizontal_lines(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple HorizontalLine in one layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _line1: HorizontalLine
            middle: QLabel = new("Middle")
            _line2: HorizontalLine

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: line, label, line
        assert_that(layout.count()).is_equal_to(3)

    def test_horizontal_line_accessible_as_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """HorizontalLine is accessible as instance attribute."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _divider: HorizontalLine
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._divider).is_instance_of(QFrame)
        assert_that(instance._divider.frameShape()).is_equal_to(QFrame.Shape.HLine)


# =============================================================================
# VerticalLine
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestVerticalLine:
    """VerticalLine adds a vertical divider (QFrame with VLine)."""

    def test_bare_vertical_line(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare `_line: VerticalLine` creates VLine QFrame."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _line: VerticalLine
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: left label, line, right label
        assert_that(layout.count()).is_equal_to(3)

        # The middle item should be a QFrame with VLine shape
        line_item = layout.itemAt(1)
        assert_that(line_item).is_not_none()
        line_widget = line_item.widget()
        assert_that(line_widget).is_instance_of(QFrame)
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_vertical_line_with_new(self, base_class, decorator, qt: QtDriver) -> None:
        """VerticalLine = new() also works."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _line: VerticalLine = new()
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)

        line_widget = layout.itemAt(1).widget()
        assert_that(line_widget).is_instance_of(QFrame)
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_vertical_line_in_vertical_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """VerticalLine in vertical layout still has VLine shape."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _line: VerticalLine
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout).is_instance_of(QVBoxLayout)
        assert_that(layout.count()).is_equal_to(3)

        line_widget = layout.itemAt(1).widget()
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_vertical_line_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """VerticalLine can target a nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _line: VerticalLine = new(layout="_row")
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)
        # Nested layout should have 3 items
        assert_that(instance._row.count()).is_equal_to(3)

        line_widget = instance._row.itemAt(1).widget()
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_multiple_vertical_lines(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple VerticalLine in one layout."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            _line1: VerticalLine
            middle: QLabel = new("Middle")
            _line2: VerticalLine

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        # 3 items: line, label, line
        assert_that(layout.count()).is_equal_to(3)

    def test_vertical_line_accessible_as_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """VerticalLine is accessible as instance attribute."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _divider: VerticalLine
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._divider).is_instance_of(QFrame)
        assert_that(instance._divider.frameShape()).is_equal_to(QFrame.Shape.VLine)


# =============================================================================
# Mixed Lines
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMixedLines:
    """Mix of HorizontalLine and VerticalLine."""

    def test_both_line_types(self, base_class, decorator, qt: QtDriver) -> None:
        """Both HorizontalLine and VerticalLine in same widget."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _hline: HorizontalLine
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _vline: VerticalLine = new(layout="_row")
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)

        # Check HLine in main layout
        assert_that(instance._hline.frameShape()).is_equal_to(QFrame.Shape.HLine)

        # Check VLine in nested layout
        assert_that(instance._vline.frameShape()).is_equal_to(QFrame.Shape.VLine)


# =============================================================================
# Line (auto-selecting based on layout orientation)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLineAutoSelect:
    """Line auto-selects HLine/VLine based on layout orientation."""

    def test_line_in_vertical_layout_becomes_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """Line in vertical layout becomes HorizontalLine."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _line: Line
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)

        line_widget = layout.itemAt(1).widget()
        assert_that(line_widget).is_instance_of(QFrame)
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_line_in_horizontal_layout_becomes_vertical(self, base_class, decorator, qt: QtDriver) -> None:
        """Line in horizontal layout becomes VerticalLine."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _line: Line
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        assert_that(layout).is_instance_of(QHBoxLayout)
        assert_that(layout.count()).is_equal_to(3)

        line_widget = layout.itemAt(1).widget()
        assert_that(line_widget).is_instance_of(QFrame)
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_line_with_new_in_vertical_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Line = new() in vertical layout becomes HorizontalLine."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _line: Line = new()
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        line_widget = get_layout(instance, base_class).itemAt(1).widget()
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_line_with_new_in_horizontal_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Line = new() in horizontal layout becomes VerticalLine."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            left: QLabel = new("Left")
            _line: Line = new()
            right: QLabel = new("Right")

        instance = create_and_track(qt, TestClass, base_class)
        line_widget = get_layout(instance, base_class).itemAt(1).widget()
        assert_that(line_widget.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_line_in_form_layout_becomes_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """Line in form layout becomes HorizontalLine (non-horizontal default)."""

        @decorator(layout="form")
        class TestClass(base_class):
            top: QLabel = new("Top", label="Top:")
            _line: Line = new()
            bottom: QLabel = new("Bottom", label="Bottom:")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._line.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_line_in_grid_layout_becomes_horizontal(self, base_class, decorator, qt: QtDriver) -> None:
        """Line in grid layout becomes HorizontalLine (non-horizontal default)."""

        @decorator(layout="grid")
        class TestClass(base_class):
            top: QLabel = new("Top", grid=(0, 0))
            _line: Line = new(grid=(1, 0))
            bottom: QLabel = new("Bottom", grid=(2, 0))

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._line.frameShape()).is_equal_to(QFrame.Shape.HLine)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLineInNestedLayout:
    """Line auto-selects based on nested layout orientation."""

    def test_line_in_nested_horizontal_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Line in nested QHBoxLayout becomes VerticalLine."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _line: Line = new(layout="_row")
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._row.count()).is_equal_to(3)
        assert_that(instance._line.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_line_in_nested_vertical_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Line in nested QVBoxLayout becomes HorizontalLine."""

        @decorator(layout="horizontal")
        class TestClass(base_class):
            _col: QVBoxLayout = new()
            top: QLabel = new("Top", layout="_col")
            _line: Line = new(layout="_col")
            bottom: QLabel = new("Bottom", layout="_col")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._col.count()).is_equal_to(3)
        assert_that(instance._line.frameShape()).is_equal_to(QFrame.Shape.HLine)

    def test_multiple_lines_in_different_layouts(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple Lines in different layout contexts get correct orientation."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _main_line: Line  # In vertical main → HLine
            _row: QHBoxLayout = new()
            left: QLabel = new("Left", layout="_row")
            _row_line: Line = new(layout="_row")  # In horizontal nested → VLine
            right: QLabel = new("Right", layout="_row")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout line should be HLine
        assert_that(instance._main_line.frameShape()).is_equal_to(QFrame.Shape.HLine)

        # Nested horizontal layout line should be VLine
        assert_that(instance._row_line.frameShape()).is_equal_to(QFrame.Shape.VLine)

    def test_line_accessible_as_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """Line is accessible as instance attribute."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            top: QLabel = new("Top")
            _divider: Line
            bottom: QLabel = new("Bottom")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._divider).is_instance_of(QFrame)
        # In vertical layout, Line becomes HLine
        assert_that(instance._divider.frameShape()).is_equal_to(QFrame.Shape.HLine)
