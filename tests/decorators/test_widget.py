from dataclasses import is_dataclass

import pytest
from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from qtpie.decorators.widget import widget, widget_class
from qtpie.types.widget_layout_type import WidgetLayoutType

# --- Decorated Widget Classes ---


@widget
class WidgetWithoutParentheses(QWidget):
    value: int


@widget()
class WidgetWithParentheses(QWidget):
    value: int


@widget_class
class PlainWidgetWithoutParentheses(QWidget):
    def __init__(self, value: int):
        super().__init__()
        self.value = value


@widget_class()
class PlainWidgetWithParentheses(QWidget):
    def __init__(self, value: int):
        super().__init__()
        self.value = value


# --- Shared Tests ---


@pytest.mark.parametrize(
    "widget_class,args,expected_name",
    [
        (WidgetWithoutParentheses, (1,), "WidgetWithoutParentheses"),
        (WidgetWithParentheses, (2,), "WidgetWithParentheses"),
        (PlainWidgetWithoutParentheses, (42,), "PlainWidgetWithoutParentheses"),
        (PlainWidgetWithParentheses, (99,), "PlainWidgetWithParentheses"),
    ],
)
class TestSharedWidgetBehavior:
    def test_constructor_and_object_name(
        self,
        qtbot: QtBot,
        widget_class: type,
        args: tuple[int, ...],
        expected_name: str,
    ) -> None:
        """Test that all widgets set object name and constructor args correctly."""
        widget_instance = widget_class(*args)
        assert_that(widget_instance.objectName()).is_equal_to(expected_name)
        assert_that(widget_instance.value).is_equal_to(args[0])

    def test_constructor_accepts_kwarg(
        self,
        qtbot: QtBot,
        widget_class: type,
        args: tuple[int, ...],
        expected_name: str,
    ) -> None:
        """Test that all widgets accept value as a keyword argument."""
        widget_instance = widget_class(value=args[0])
        assert_that(widget_instance.objectName()).is_equal_to(expected_name)
        assert_that(widget_instance.value).is_equal_to(args[0])


# --- Decorator-Specific Tests ---


@pytest.mark.parametrize(
    "widget_class,args",
    [
        (WidgetWithoutParentheses, (1,)),
        (WidgetWithParentheses, (2,)),
    ],
)
class TestDataclassWidgets:
    def test_makes_dataclass(
        self,
        qtbot: QtBot,
        widget_class: type,
        args: tuple[int, ...],
    ) -> None:
        widget_instance = widget_class(*args)
        assert_that(is_dataclass(widget_class)).is_true()
        assert_that(is_dataclass(widget_instance)).is_true()


@pytest.mark.parametrize(
    "widget_class,args",
    [
        (PlainWidgetWithoutParentheses, (42,)),
        (PlainWidgetWithParentheses, (99,)),
    ],
)
class TestPlainWidgets:
    def test_not_dataclass(
        self,
        qtbot: QtBot,
        widget_class: type,
        args: tuple[int, ...],
    ) -> None:
        widget_instance = widget_class(*args)
        assert_that(is_dataclass(widget_class)).is_false()
        assert_that(is_dataclass(widget_instance)).is_false()


# --- Custom Name Tests ---


@widget(name="CustomDataclassWidget")
class WidgetWithCustomName(QWidget):
    value: int


@widget_class(name="CustomPlainWidget")
class PlainWidgetWithCustomName(QWidget):
    def __init__(self, value: int):
        super().__init__()
        self.value = value


class TestCustomObjectNames:
    def test_widget_custom_name(self) -> None:
        widget = WidgetWithCustomName(42)
        assert_that(widget.objectName()).is_equal_to("CustomDataclassWidget")

    def test_widget_class_custom_name(self) -> None:
        widget = PlainWidgetWithCustomName(42)
        assert_that(widget.objectName()).is_equal_to("CustomPlainWidget")


# --- Layout Parameter Tests ---


@pytest.mark.parametrize(
    "layout_str,layout_cls",
    [
        ("horizontal", QHBoxLayout),
        ("vertical", QVBoxLayout),
        ("grid", QGridLayout),
        ("form", QFormLayout),
    ],
)
def test_widget_layout_sets_correct_layout(qtbot: QtBot, layout_str: WidgetLayoutType, layout_cls: type) -> None:
    @widget(layout=layout_str)
    class TestWidget(QWidget):
        pass

    widget_instance = TestWidget()
    qtbot.addWidget(widget_instance)
    assert_that(widget_instance.layout()).is_instance_of(layout_cls)


def test_widget_default_layout_is_vertical(qtbot: QtBot) -> None:
    """Test that the default layout is QVBoxLayout when not specified."""

    @widget
    class DefaultLayoutWidget(QWidget):
        pass

    widget_instance = DefaultLayoutWidget()
    qtbot.addWidget(widget_instance)
    assert_that(widget_instance.layout()).is_instance_of(QVBoxLayout)


def test_widget_class_default_layout_is_vertical(qtbot: QtBot) -> None:
    """Test that the default layout is QVBoxLayout for @widget_class when not specified."""

    @widget_class
    class DefaultLayoutWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()

    widget_instance = DefaultLayoutWidget()
    qtbot.addWidget(widget_instance)
    assert_that(widget_instance.layout()).is_instance_of(QVBoxLayout)


@pytest.mark.parametrize(
    "layout_str,layout_cls",
    [
        ("horizontal", QHBoxLayout),
        ("vertical", QVBoxLayout),
        ("grid", QGridLayout),
        ("form", QFormLayout),
    ],
)
def test_widget_class_layout_sets_correct_layout(qtbot: QtBot, layout_str: WidgetLayoutType, layout_cls: type) -> None:
    @widget_class(layout=layout_str)
    class TestWidget(QWidget):
        pass

    widget_instance = TestWidget()
    qtbot.addWidget(widget_instance)
    assert_that(widget_instance.layout()).is_instance_of(layout_cls)


@pytest.mark.parametrize(
    "decorator",
    [
        lambda c: widget(layout=None)(c),
        lambda c: widget_class(layout=None)(c),
    ],
)
def test_layout_parameter_none_sets_no_layout(qtbot: QtBot, decorator) -> None:
    """Test that layout=None does not set a layout."""

    class TestWidget(QWidget):
        pass

    Decorated = decorator(TestWidget)
    widget_instance = Decorated()
    qtbot.addWidget(widget_instance)
    assert_that(widget_instance.layout()).is_none()


# --- Validation Tests ---


class TestWidgetValidation:
    def test_widget_rejects_non_qwidget(self) -> None:
        """Test that @widget decorator rejects classes that don't inherit from QWidget."""
        with pytest.raises(TypeError, match="@widget can only be applied to QWidget subclasses"):

            @widget
            class NotAWidget:  # type: ignore
                pass
