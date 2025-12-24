# IMPORTANT: If you add or change a test here, you MUST add or change a corresponding test
# in test_widget_class_decorator.py! These two files are meant to have parallel coverage
# for @widget and @widget_class. Do NOT add a test to only one file unless it is
# absolutely unique to that decorator. Keep them in sync!

from dataclasses import is_dataclass

from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QFormLayout, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from qtpie.decorators.widget import widget
from qtpie.styles.classes import get_classes


def test_is_dataclass(qtbot: QtBot) -> None:
    @widget
    class SimpleWidget(QWidget):
        value: int = 42

    assert_that(is_dataclass(SimpleWidget)).is_true()
    assert_that(is_dataclass(SimpleWidget())).is_true()


def test_field_defaults(qtbot: QtBot) -> None:
    @widget
    class SimpleWidget(QWidget):
        value: int = 42

    widget_instance = SimpleWidget()
    assert_that(widget_instance.value).is_equal_to(42)


def test_accepts_kwarg(qtbot: QtBot) -> None:
    @widget
    class SimpleWidget(QWidget):
        value: int = 42

    widget_instance = SimpleWidget(value=99)
    assert_that(widget_instance.value).is_equal_to(99)


def test_multi_field_defaults(qtbot: QtBot) -> None:
    @widget
    class MultiFieldWidget(QWidget):
        name: str = "default"
        count: int = 0

    widget_instance = MultiFieldWidget()
    assert_that(widget_instance.name).is_equal_to("default")
    assert_that(widget_instance.count).is_equal_to(0)


def test_layout_mode_vertical(qtbot: QtBot) -> None:
    @widget(layout="vertical")
    class VerticalWidget(QWidget):
        pass

    widget_instance = VerticalWidget()
    assert_that(widget_instance.layout()).is_instance_of(QVBoxLayout)


def test_layout_mode_horizontal(qtbot: QtBot) -> None:
    @widget(layout="horizontal")
    class HorizontalWidget(QWidget):
        pass

    widget_instance = HorizontalWidget()
    assert_that(widget_instance.layout()).is_instance_of(QHBoxLayout)


def test_layout_mode_grid(qtbot: QtBot) -> None:
    @widget(layout="grid")
    class GridWidget(QWidget):
        pass

    widget_instance = GridWidget()
    assert_that(widget_instance.layout()).is_instance_of(QGridLayout)


def test_layout_mode_form(qtbot: QtBot) -> None:
    @widget(layout="form")
    class FormWidget(QWidget):
        pass

    widget_instance = FormWidget()
    assert_that(widget_instance.layout()).is_instance_of(QFormLayout)


def test_named_widget_name(qtbot: QtBot) -> None:
    @widget
    class NamedWidget(QWidget):
        name: str = "CustomWidgetName"

    widget_instance = NamedWidget()
    assert_that(widget_instance.name).is_equal_to("CustomWidgetName")


def test_classes_default_empty(qtbot: QtBot) -> None:
    @widget
    class NoClassWidget(QWidget):
        pass

    widget_instance = NoClassWidget()
    assert_that(get_classes(widget_instance)).is_empty()


def test_classes_explicit(qtbot: QtBot) -> None:
    @widget(classes=["foo", "bar"])
    class WithClassWidget(QWidget):
        pass

    widget_instance = WithClassWidget()
    assert_that(get_classes(widget_instance)).is_equal_to(["foo", "bar"])


def test_widget_labelwidget_sets_text(qtbot: QtBot) -> None:
    """Test @widget with a dataclass QLabel and __post_init__."""

    @widget
    class LabelWidget(QLabel):
        text_value: str

        def __post_init__(self) -> None:
            self.setText(self.text_value)

    label_widget = LabelWidget("Hello")
    assert_that(label_widget.text()).is_equal_to("Hello")


def test_layout_vertical_adds_widgets(qtbot: QtBot) -> None:
    """Test @widget with vertical layout adds widgets from factories."""
    from qtpy.QtWidgets import QLineEdit

    from qtpie.factories.dataclass_factories.make import make

    @widget(layout="vertical")
    class VerticalWidget(QWidget):
        label: QLabel = make((QLabel, "my-label", ["title"]), "Hello")
        input: QLineEdit = make(QLineEdit)

    widget_instance = VerticalWidget()
    layout = widget_instance.layout()
    assert_that(layout.count()).is_equal_to(2)
    assert_that(widget_instance.label.objectName()).is_equal_to("my-label")
    assert_that(get_classes(widget_instance.label)).contains("title")
    assert_that(widget_instance.label.text()).is_equal_to("Hello")


def test_layout_form_adds_rows_and_sets_object_name(qtbot: QtBot) -> None:
    """Test @widget with form layout adds rows with labels."""
    from qtpy.QtWidgets import QLineEdit

    from qtpie.factories.dataclass_factories.form_row import form_row

    @widget(layout="form")
    class FormWidget(QWidget):
        name: QLineEdit = form_row("Name", (QLineEdit, "name-field"))
        email: QLineEdit = form_row("Email", (QLineEdit, "email-field", ["input", "email"]))

    widget_instance = FormWidget()
    layout = widget_instance.layout()
    assert_that(layout.rowCount()).is_equal_to(2)
    assert_that(widget_instance.name.objectName()).is_equal_to("name-field")
    assert_that(widget_instance.email.objectName()).is_equal_to("email-field")
    assert_that(get_classes(widget_instance.email)).contains("input", "email")


def test_layout_grid_places_widget_correctly(qtbot: QtBot) -> None:
    """Test @widget with grid layout places widgets at correct positions."""
    from qtpy.QtWidgets import QLineEdit

    from qtpie.factories.dataclass_factories.grid_item import grid_item
    from qtpie.factories.grid_position import GridPosition

    @widget(layout="grid")
    class GridWidget(QWidget):
        field: QLineEdit = grid_item(GridPosition(2, 3), (QLineEdit, "grid-field"))

    widget_instance = GridWidget()
    layout = widget_instance.layout()
    item = layout.itemAtPosition(2, 3)
    assert_that(item).is_not_none()
    assert_that(item.widget()).is_equal_to(widget_instance.field)
    assert_that(widget_instance.field.objectName()).is_equal_to("grid-field")


def test_layout_horizontal_adds_widgets_in_order(qtbot: QtBot) -> None:
    """Test @widget with horizontal layout adds widgets in order."""
    from qtpie.factories.dataclass_factories.make import make

    @widget(layout="horizontal")
    class HorizontalWidget(QWidget):
        left: QLabel = make(QLabel, "Left")
        right: QLabel = make(QLabel, "Right")

    widget_instance = HorizontalWidget()
    layout = widget_instance.layout()
    assert_that(layout.count()).is_equal_to(2)
    assert_that(layout.itemAt(0).widget().text()).is_equal_to("Left")
    assert_that(layout.itemAt(1).widget().text()).is_equal_to("Right")
