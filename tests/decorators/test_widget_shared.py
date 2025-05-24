import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QVBoxLayout

from qtpie.decorators.widget import widget, widget_class
from tests.decorators._test_helpers import assert_layout, make_decorated


@pytest.mark.parametrize("decorator", [widget, widget_class])
@pytest.mark.parametrize(
    "name",
    [None, "CustomWidgetName"],
)
def test_sets_object_name(decorator, name: str | None) -> None:
    TestWidget = make_decorated(decorator, name=name)
    widget_instance = TestWidget()
    expected_name = name or "TestWidget"
    assert_that(widget_instance.objectName()).is_equal_to(expected_name)


@pytest.mark.parametrize("decorator", [widget, widget_class])
@pytest.mark.parametrize(
    "layout_str,layout_cls",
    [
        ("horizontal", QHBoxLayout),
        ("vertical", QVBoxLayout),
        ("grid", QGridLayout),
        ("form", QFormLayout),
    ],
)
def test_layout_parameter_sets_layout(decorator, layout_str: str, layout_cls: type) -> None:
    TestWidget = make_decorated(decorator, layout=layout_str)
    widget_instance = TestWidget()
    assert_layout(widget_instance, layout_cls)


@pytest.mark.parametrize("decorator", [widget, widget_class])
def test_layout_none_sets_no_layout(decorator) -> None:
    TestWidget = make_decorated(decorator, layout=None)
    widget_instance = TestWidget()
    assert_that(widget_instance.layout()).is_none()


@pytest.mark.parametrize("decorator", [widget, widget_class])
def test_accepts_constructor_args(decorator) -> None:
    TestWidget = make_decorated(decorator)
    widget_instance = TestWidget()
    assert_that(widget_instance.value).is_equal_to(42)


@pytest.mark.parametrize("decorator", [widget])
def test_accepts_kwargs(decorator) -> None:
    TestWidget = make_decorated(decorator)
    widget_instance = TestWidget(value=99)
    assert_that(widget_instance.value).is_equal_to(99)


@pytest.mark.parametrize("decorator", [widget, widget_class])
def test_rejects_non_qwidget(decorator) -> None:
    with pytest.raises(TypeError, match="can only be applied to QWidget subclasses"):

        @decorator
        class NotAWidget:
            pass
