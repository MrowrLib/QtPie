# IMPORTANT: If you add or change a test here, you MUST add or change a corresponding test
# in test_widget_decorator.py! These two files are meant to have parallel coverage
# for @widget_class and @widget. Do NOT add a test to only one file unless it is
# absolutely unique to that decorator. Keep them in sync!

from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QVBoxLayout, QWidget

from qtpie.decorators.widget import widget_class


def test_widget_class_no_init_sets_up_qwidget(qtbot: QtBot) -> None:
    """Test @widget_class with no __init__ (should auto-call QWidget.__init__)."""

    @widget_class
    class NoInitWidget(QWidget):
        pass

    widget = NoInitWidget()
    assert_that(widget.objectName()).is_equal_to("NoInitWidget")
    assert_that(widget.layout()).is_instance_of(QVBoxLayout)


def test_widget_class_labelwidget_no_init_sets_text(qtbot: QtBot) -> None:
    """Test @widget_class with QLabel and no __init__, should set text via constructor."""

    from qtpy.QtWidgets import QLabel

    @widget_class
    class LabelWidgetNoInit(QLabel):
        pass

    widget = LabelWidgetNoInit("Hello")
    assert_that(widget.text()).is_equal_to("Hello")


def test_widget_class_custom_init_calls_super(qtbot: QtBot) -> None:
    """Test @widget_class with custom __init__ that calls super().__init__()."""

    @widget_class
    class CustomInitWidget(QWidget):
        def __init__(self) -> None:
            super().__init__()

    widget = CustomInitWidget()
    assert_that(widget.objectName()).is_equal_to("CustomInitWidget")
    assert_that(widget.layout()).is_instance_of(QVBoxLayout)


def test_widget_class_labelwidget_custom_init_sets_text(qtbot: QtBot) -> None:
    """Test @widget_class with QLabel and custom __init__."""

    from qtpy.QtWidgets import QLabel

    @widget_class
    class LabelWidgetCustomInit(QLabel):
        def __init__(self, number: int) -> None:
            super().__init__(f"The number is: {number}")

    widget = LabelWidgetCustomInit(42)
    assert_that(widget.text()).is_equal_to("The number is: 42")


def test_layout_vertical_adds_widgets(qtbot: QtBot) -> None:
    """Test @widget_class with vertical layout adds widgets from factories."""
    from qtpy.QtWidgets import QLabel, QLineEdit

    from qtpie.factories.attribute_factories.make import make

    @widget_class(layout="vertical")
    class VerticalWidget(QWidget):
        label: QLabel
        input: QLineEdit

        def __init__(self) -> None:
            super().__init__()
            self.label = make((QLabel, "my-label", ["title"]), "Hello")
            self.input = make(QLineEdit)

    widget = VerticalWidget()
    layout = widget.layout()
    assert layout is not None
    assert_that(layout.count()).is_equal_to(2)
    assert_that(widget.label.objectName()).is_equal_to("my-label")
    from qtpie.styles.classes import get_classes

    assert_that(get_classes(widget.label)).contains("title")
    assert_that(widget.label.text()).is_equal_to("Hello")


def test_layout_form_adds_rows_and_sets_object_name(qtbot: QtBot) -> None:
    """Test @widget_class with form layout adds rows with labels."""
    from qtpy.QtWidgets import QFormLayout, QLineEdit

    from qtpie.factories.attribute_factories.form_row import form_row

    @widget_class(layout="form")
    class FormWidget(QWidget):
        name: QLineEdit
        email: QLineEdit

        def __init__(self) -> None:
            super().__init__()
            self.name = form_row("Name", (QLineEdit, "name-field"))
            self.email = form_row("Email", (QLineEdit, "email-field", ["input", "email"]))

    widget = FormWidget()
    layout = widget.layout()
    assert layout is not None
    assert isinstance(layout, QFormLayout)
    assert_that(layout.rowCount()).is_equal_to(2)
    assert_that(widget.name.objectName()).is_equal_to("name-field")
    assert_that(widget.email.objectName()).is_equal_to("email-field")
    from qtpie.styles.classes import get_classes

    assert_that(get_classes(widget.email)).contains("input", "email")


def test_layout_grid_places_widget_correctly(qtbot: QtBot) -> None:
    """Test @widget_class with grid layout places widgets at correct positions."""
    from qtpy.QtWidgets import QGridLayout, QLineEdit

    from qtpie.factories.attribute_factories.grid_item import grid_item
    from qtpie.factories.grid_position import GridPosition

    @widget_class(layout="grid")
    class GridWidget(QWidget):
        field: QLineEdit

        def __init__(self) -> None:
            super().__init__()
            self.field = grid_item(GridPosition(2, 3), (QLineEdit, "grid-field"))

    widget = GridWidget()
    layout = widget.layout()
    assert layout is not None
    assert isinstance(layout, QGridLayout)
    item = layout.itemAtPosition(2, 3)
    assert_that(item).is_not_none()
    assert item is not None
    assert_that(item.widget()).is_equal_to(widget.field)
    assert_that(widget.field.objectName()).is_equal_to("grid-field")


def test_layout_horizontal_adds_widgets_in_order(qtbot: QtBot) -> None:
    """Test @widget_class with horizontal layout adds widgets in order."""
    from qtpy.QtWidgets import QLabel

    from qtpie.factories.attribute_factories.make import make

    @widget_class(layout="horizontal")
    class HorizontalWidget(QWidget):
        left: QLabel
        right: QLabel

        def __init__(self) -> None:
            super().__init__()
            self.left = make(QLabel, "Left")
            self.right = make(QLabel, "Right")

    widget = HorizontalWidget()
    layout = widget.layout()
    assert layout is not None
    assert_that(layout.count()).is_equal_to(2)
    item0 = layout.itemAt(0)
    item1 = layout.itemAt(1)
    assert item0 is not None
    assert item1 is not None
    assert_that(item0.widget().text()).is_equal_to("Left")
    assert_that(item1.widget().text()).is_equal_to("Right")
