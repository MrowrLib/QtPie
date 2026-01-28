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
"""Tests for margins on decorators and per-widget margins via new().

Tests both:
- Decorator-level margins (margins=, marginLeft=, etc.) on @widget, @window, etc.
- Per-widget margins (margin=, marginLeft=, etc.) on new() for individual fields.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QFrame, QGroupBox, QLabel, QPushButton, QSplitter

from qtpie import Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track, get_layout

# =============================================================================
# Decorator-level individual margins (marginLeft=, marginTop=, etc.)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestIndividualMargins:
    """Test marginLeft, marginTop, marginRight, marginBottom kwargs on decorators."""

    def test_margins_default_zero(self, base_class, decorator, qt: QtDriver) -> None:
        """Default margins are 0 on all sides."""

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(0)

    def test_margins_int_all_sides(self, base_class, decorator, qt: QtDriver) -> None:
        """margins=N applies N to all sides."""

        @decorator(margins=10)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(10)
        assert_that(m.top()).is_equal_to(10)
        assert_that(m.right()).is_equal_to(10)
        assert_that(m.bottom()).is_equal_to(10)

    def test_margins_tuple(self, base_class, decorator, qt: QtDriver) -> None:
        """margins=(left, top, right, bottom) applies each side."""

        @decorator(margins=(1, 2, 3, 4))
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(1)
        assert_that(m.top()).is_equal_to(2)
        assert_that(m.right()).is_equal_to(3)
        assert_that(m.bottom()).is_equal_to(4)

    def test_marginLeft_only(self, base_class, decorator, qt: QtDriver) -> None:
        """marginLeft overrides left, others stay at margins default."""

        @decorator(marginLeft=20)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(20)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(0)

    def test_marginTop_only(self, base_class, decorator, qt: QtDriver) -> None:
        """marginTop overrides top, others stay at margins default."""

        @decorator(marginTop=15)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(15)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(0)

    def test_marginRight_only(self, base_class, decorator, qt: QtDriver) -> None:
        """marginRight overrides right, others stay at margins default."""

        @decorator(marginRight=25)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(25)
        assert_that(m.bottom()).is_equal_to(0)

    def test_marginBottom_only(self, base_class, decorator, qt: QtDriver) -> None:
        """marginBottom overrides bottom, others stay at margins default."""

        @decorator(marginBottom=30)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(30)

    def test_individual_margins_override_int(self, base_class, decorator, qt: QtDriver) -> None:
        """Individual margins override the corresponding side of margins=int."""

        @decorator(margins=10, marginLeft=5, marginBottom=20)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(5)
        assert_that(m.top()).is_equal_to(10)
        assert_that(m.right()).is_equal_to(10)
        assert_that(m.bottom()).is_equal_to(20)

    def test_individual_margins_override_tuple(self, base_class, decorator, qt: QtDriver) -> None:
        """Individual margins override the corresponding side of margins=tuple."""

        @decorator(margins=(1, 2, 3, 4), marginTop=99, marginRight=88)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(1)
        assert_that(m.top()).is_equal_to(99)
        assert_that(m.right()).is_equal_to(88)
        assert_that(m.bottom()).is_equal_to(4)

    def test_all_individual_margins(self, base_class, decorator, qt: QtDriver) -> None:
        """All four individual margins set independently."""

        @decorator(marginLeft=10, marginTop=20, marginRight=30, marginBottom=40)
        class TestClass(base_class):
            label: QLabel = new("Hello")

        instance = create_and_track(qt, TestClass, base_class)
        layout = get_layout(instance, base_class)
        m = layout.contentsMargins()
        assert_that(m.left()).is_equal_to(10)
        assert_that(m.top()).is_equal_to(20)
        assert_that(m.right()).is_equal_to(30)
        assert_that(m.bottom()).is_equal_to(40)


# =============================================================================
# Per-widget margins via new() (margin=, marginLeft=, etc.)
# =============================================================================


class TestPerWidgetMargins:
    """Test margin=, marginLeft=, marginTop=, marginRight=, marginBottom= on new()."""

    def test_margin_int_all_sides(self, qt: QtDriver) -> None:
        """margin=N on new() applies N to all sides of the widget."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", margin=10)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(10)
        assert_that(m.top()).is_equal_to(10)
        assert_that(m.right()).is_equal_to(10)
        assert_that(m.bottom()).is_equal_to(10)

    def test_margin_tuple(self, qt: QtDriver) -> None:
        """margin=(left, top, right, bottom) on new() applies each side."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", margin=(1, 2, 3, 4))

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(1)
        assert_that(m.top()).is_equal_to(2)
        assert_that(m.right()).is_equal_to(3)
        assert_that(m.bottom()).is_equal_to(4)

    def test_marginLeft_only(self, qt: QtDriver) -> None:
        """marginLeft= on new() sets only left margin, others default to 0."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", marginLeft=20)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(20)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(0)

    def test_marginTop_only(self, qt: QtDriver) -> None:
        """marginTop= on new() sets only top margin."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", marginTop=15)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(15)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(0)

    def test_marginRight_only(self, qt: QtDriver) -> None:
        """marginRight= on new() sets only right margin."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", marginRight=25)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(25)
        assert_that(m.bottom()).is_equal_to(0)

    def test_marginBottom_only(self, qt: QtDriver) -> None:
        """marginBottom= on new() sets only bottom margin."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", marginBottom=30)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(30)

    def test_margin_int_with_individual_overrides(self, qt: QtDriver) -> None:
        """Individual margins override the corresponding side of margin=int."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", margin=10, marginLeft=5, marginBottom=20)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(5)
        assert_that(m.top()).is_equal_to(10)
        assert_that(m.right()).is_equal_to(10)
        assert_that(m.bottom()).is_equal_to(20)

    def test_margin_tuple_with_individual_overrides(self, qt: QtDriver) -> None:
        """Individual margins override the corresponding side of margin=tuple."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", margin=(1, 2, 3, 4), marginTop=99, marginRight=88)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(1)
        assert_that(m.top()).is_equal_to(99)
        assert_that(m.right()).is_equal_to(88)
        assert_that(m.bottom()).is_equal_to(4)

    def test_all_individual_margins(self, qt: QtDriver) -> None:
        """All four individual margins set independently on new()."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello", marginLeft=10, marginTop=20, marginRight=30, marginBottom=40)

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m.left()).is_equal_to(10)
        assert_that(m.top()).is_equal_to(20)
        assert_that(m.right()).is_equal_to(30)
        assert_that(m.bottom()).is_equal_to(40)

    def test_no_margin_leaves_widget_default(self, qt: QtDriver) -> None:
        """Without margin kwargs, widget retains its default margins."""

        @widget
        class TestClass(Widget):
            label: QLabel = new("Hello")

        instance = TestClass()
        qt.track(instance)
        m = instance.label.contentsMargins()
        assert_that(m).is_not_none()

    def test_multiple_widgets_different_margins(self, qt: QtDriver) -> None:
        """Different widgets can have different per-widget margins."""

        @widget
        class TestClass(Widget):
            label1: QLabel = new("First", margin=5)
            label2: QLabel = new("Second", margin=15)
            label3: QLabel = new("Third", marginTop=10, marginBottom=20)

        instance = TestClass()
        qt.track(instance)

        m1 = instance.label1.contentsMargins()
        assert_that(m1.left()).is_equal_to(5)
        assert_that(m1.top()).is_equal_to(5)
        assert_that(m1.right()).is_equal_to(5)
        assert_that(m1.bottom()).is_equal_to(5)

        m2 = instance.label2.contentsMargins()
        assert_that(m2.left()).is_equal_to(15)
        assert_that(m2.top()).is_equal_to(15)
        assert_that(m2.right()).is_equal_to(15)
        assert_that(m2.bottom()).is_equal_to(15)

        m3 = instance.label3.contentsMargins()
        assert_that(m3.left()).is_equal_to(0)
        assert_that(m3.top()).is_equal_to(10)
        assert_that(m3.right()).is_equal_to(0)
        assert_that(m3.bottom()).is_equal_to(20)

    def test_per_widget_margin_with_button(self, qt: QtDriver) -> None:
        """margin= works on QPushButton."""

        @widget
        class TestClass(Widget):
            btn: QPushButton = new("Click", margin=8)

        instance = TestClass()
        qt.track(instance)
        m = instance.btn.contentsMargins()
        assert_that(m.left()).is_equal_to(8)
        assert_that(m.top()).is_equal_to(8)
        assert_that(m.right()).is_equal_to(8)
        assert_that(m.bottom()).is_equal_to(8)

    def test_per_widget_margin_on_qframe(self, qt: QtDriver) -> None:
        """margin= works on QFrame (has early return in __set_name__)."""

        @widget
        class TestClass(Widget):
            divider: QFrame = new(frameShape=QFrame.Shape.HLine, marginBottom=100)

        instance = TestClass()
        qt.track(instance)
        m = instance.divider.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(100)

    def test_per_widget_margin_on_qframe_all_sides(self, qt: QtDriver) -> None:
        """margin=N on QFrame applies to all sides."""

        @widget
        class TestClass(Widget):
            divider: QFrame = new(frameShape=QFrame.Shape.HLine, margin=12)

        instance = TestClass()
        qt.track(instance)
        m = instance.divider.contentsMargins()
        assert_that(m.left()).is_equal_to(12)
        assert_that(m.top()).is_equal_to(12)
        assert_that(m.right()).is_equal_to(12)
        assert_that(m.bottom()).is_equal_to(12)

    def test_per_widget_margin_on_qgroupbox(self, qt: QtDriver) -> None:
        """margin= works on QGroupBox (has early return in __set_name__)."""

        @widget
        class TestClass(Widget):
            group: QGroupBox = new("Settings", margin=7)

        instance = TestClass()
        qt.track(instance)
        m = instance.group.contentsMargins()
        assert_that(m.left()).is_equal_to(7)
        assert_that(m.top()).is_equal_to(7)
        assert_that(m.right()).is_equal_to(7)
        assert_that(m.bottom()).is_equal_to(7)

    def test_per_widget_margin_on_qgroupbox_individual(self, qt: QtDriver) -> None:
        """Individual margins work on QGroupBox."""

        @widget
        class TestClass(Widget):
            group: QGroupBox = new("Settings", marginLeft=5, marginRight=10)

        instance = TestClass()
        qt.track(instance)
        m = instance.group.contentsMargins()
        assert_that(m.left()).is_equal_to(5)
        assert_that(m.top()).is_equal_to(0)
        assert_that(m.right()).is_equal_to(10)
        assert_that(m.bottom()).is_equal_to(0)

    def test_per_widget_margin_on_qsplitter(self, qt: QtDriver) -> None:
        """margin= works on QSplitter (has early return in __set_name__)."""

        @widget
        class TestClass(Widget):
            split: QSplitter = new(margin=6)

        instance = TestClass()
        qt.track(instance)
        m = instance.split.contentsMargins()
        assert_that(m.left()).is_equal_to(6)
        assert_that(m.top()).is_equal_to(6)
        assert_that(m.right()).is_equal_to(6)
        assert_that(m.bottom()).is_equal_to(6)

    def test_per_widget_margin_on_qsplitter_individual(self, qt: QtDriver) -> None:
        """Individual margins work on QSplitter."""

        @widget
        class TestClass(Widget):
            split: QSplitter = new(marginTop=15, marginBottom=25)

        instance = TestClass()
        qt.track(instance)
        m = instance.split.contentsMargins()
        assert_that(m.left()).is_equal_to(0)
        assert_that(m.top()).is_equal_to(15)
        assert_that(m.right()).is_equal_to(0)
        assert_that(m.bottom()).is_equal_to(25)
