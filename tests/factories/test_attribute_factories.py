from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QLabel

from qtpie.factories.attribute_factories.form_row import make as form_row
from qtpie.factories.attribute_factories.grid_item import make as grid_item
from qtpie.factories.attribute_factories.make import make


class TestAttributeMakeFactory:
    def test_make_with_type_only(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make(QLabel)

        assert_that(Form.__annotations__).contains("label")
        assert_that(Form.__annotations__["label"]).is_equal_to(QLabel)

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_none()
        assert_that(props.class_names).is_empty()

    def test_make_with_type_and_id(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make((QLabel, "CoolLabel"))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_make_with_type_and_classes(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make((QLabel, ["class-one"]))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_make_with_type_id_and_classes(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make((QLabel, "CoolLabel", ["class-one", "class-two"]))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])

    def test_make_with_args(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make(QLabel, "Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")

    def test_make_with_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make(QLabel, text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")

    def test_make_with_type_and_id_with_args(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make((QLabel, "CoolLabel"), "Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_make_with_type_and_classes_with_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make((QLabel, ["class-one"]), text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_make_with_type_id_and_classes_with_args_and_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = make((QLabel, "CoolLabel", ["class-one", "class-two"]), text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])


class TestAttributeFormRowFactory:
    def test_form_row_with_type_only(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", QLabel)

        assert_that(Form.__annotations__).contains("label")
        assert_that(Form.__annotations__["label"]).is_equal_to(QLabel)

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_none()
        assert_that(props.class_names).is_empty()

    def test_form_row_with_type_and_id(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", (QLabel, "CoolLabel"))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_form_row_with_type_and_classes(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", (QLabel, ["class-one"]))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_form_row_with_type_id_and_classes(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", (QLabel, "CoolLabel", ["class-one", "class-two"]))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])

    def test_form_row_with_args(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", QLabel, "Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")

    def test_form_row_with_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", QLabel, text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")

    def test_form_row_with_type_and_id_with_args(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", (QLabel, "CoolLabel"), "Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_form_row_with_type_and_classes_with_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", (QLabel, ["class-one"]), text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_form_row_with_type_id_and_classes_with_args_and_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = form_row("Name", (QLabel, "CoolLabel", ["class-one", "class-two"]), text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])


class TestAttributeGridItemFactory:
    def test_grid_item_with_type_only(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), QLabel)

        assert_that(Form.__annotations__).contains("label")
        assert_that(Form.__annotations__["label"]).is_equal_to(QLabel)

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_none()
        assert_that(props.class_names).is_empty()

    def test_grid_item_with_type_and_id(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), (QLabel, "CoolLabel"))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_grid_item_with_type_and_classes(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), (QLabel, ["class-one"]))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_grid_item_with_type_id_and_classes(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), (QLabel, "CoolLabel", ["class-one", "class-two"]))

        form = Form()
        qtbot.addWidget(form.label)
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])

    def test_grid_item_with_args(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), QLabel, "Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))

    def test_grid_item_with_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), QLabel, text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))

    def test_grid_item_with_type_and_id_with_args(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), (QLabel, "CoolLabel"), "Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_grid_item_with_type_and_classes_with_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), (QLabel, ["class-one"]), text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_grid_item_with_type_id_and_classes_with_args_and_kwargs(self, qtbot: QtBot) -> None:
        class Form:
            label: QLabel

            def __init__(self) -> None:
                self.label = grid_item((0, 1), (QLabel, "CoolLabel", ["class-one", "class-two"]), text="Default text")

        form = Form()
        qtbot.addWidget(form.label)
        assert_that(form.label.text()).is_equal_to("Default text")
        props = form.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])
