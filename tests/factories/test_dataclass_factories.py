from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel

from qtpie.factories.dataclass_factories.form_row import form_row
from qtpie.factories.dataclass_factories.grid_item import grid_item
from qtpie.factories.dataclass_factories.make import make


class TestDataclassMakeFactory:
    def test_make_with_type_only(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make(QLabel)

        assert_that(Form.__annotations__).contains("label")
        assert_that(Form.__annotations__["label"]).is_equal_to(QLabel)

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_none()
        assert_that(props.class_names).is_none()

    def test_make_with_type_and_id(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make((QLabel, "CoolLabel"))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_make_with_type_and_classes(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make((QLabel, ["class-one"]))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_make_with_type_id_and_classes(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make((QLabel, "CoolLabel", ["class-one", "class-two"]))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])

    def test_make_with_args(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make(QLabel, "Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")

    def test_make_with_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make(QLabel, text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")

    def test_make_with_type_and_id_with_args(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make((QLabel, "CoolLabel"), "Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_make_with_type_and_classes_with_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make((QLabel, ["class-one"]), text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_make_with_type_id_and_classes_with_args_and_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = make((QLabel, "CoolLabel", ["class-one", "class-two"]), text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])


class TestDataclassFormRowFactory:
    def test_form_row_with_type_only(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", QLabel)

        assert_that(Form.__annotations__).contains("label")
        assert_that(Form.__annotations__["label"]).is_equal_to(QLabel)

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_none()
        assert_that(props.class_names).is_none()

    def test_form_row_with_type_and_id(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", (QLabel, "CoolLabel"))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_form_row_with_type_and_classes(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", (QLabel, ["class-one"]))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_form_row_with_type_id_and_classes(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", (QLabel, "CoolLabel", ["class-one", "class-two"]))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])

    def test_form_row_with_args(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", QLabel, "Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")

    def test_form_row_with_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", QLabel, text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")

    def test_form_row_with_type_and_id_with_args(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", (QLabel, "CoolLabel"), "Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_form_row_with_type_and_classes_with_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", (QLabel, ["class-one"]), text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_form_row_with_type_id_and_classes_with_args_and_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = form_row("Name", (QLabel, "CoolLabel", ["class-one", "class-two"]), text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.form_field_label).is_equal_to("Name")
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])


class TestDataclassGridItemFactory:
    def test_grid_item_with_type_only(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), QLabel)

        assert_that(Form.__annotations__).contains("label")
        assert_that(Form.__annotations__["label"]).is_equal_to(QLabel)

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_none()
        assert_that(props.class_names).is_none()

    def test_grid_item_with_type_and_id(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), (QLabel, "CoolLabel"))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_grid_item_with_type_and_classes(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), (QLabel, ["class-one"]))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_grid_item_with_type_id_and_classes(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), (QLabel, "CoolLabel", ["class-one", "class-two"]))

        instance = Form()
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])

    def test_grid_item_with_args(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), QLabel, "Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))

    def test_grid_item_with_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), QLabel, text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))

    def test_grid_item_with_type_and_id_with_args(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), (QLabel, "CoolLabel"), "Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")

    def test_grid_item_with_type_and_classes_with_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), (QLabel, ["class-one"]), text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.class_names).is_equal_to(["class-one"])

    def test_grid_item_with_type_id_and_classes_with_args_and_kwargs(self) -> None:
        @dataclass
        class Form:
            label: QLabel = grid_item((0, 1), (QLabel, "CoolLabel", ["class-one", "class-two"]), text="Default text")

        instance = Form()
        assert_that(instance.label.text()).is_equal_to("Default text")
        props = instance.label.property("widgetFactoryProperties")
        assert_that(props.grid_position).is_equal_to((0, 1))
        assert_that(props.object_name).is_equal_to("CoolLabel")
        assert_that(props.class_names).is_equal_to(["class-one", "class-two"])
