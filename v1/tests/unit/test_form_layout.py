"""Tests for form layout support."""

from assertpy import assert_that
from qtpy.QtWidgets import QFormLayout, QLabel, QLineEdit, QSpinBox, QWidget

from qtpie import Widget, make, widget
from qtpie.testing import QtDriver


class TestFormLayout:
    """Phase 2: Form layout functionality."""

    def test_form_layout_creates_qformlayout(self, qt: QtDriver) -> None:
        """layout='form' should create a QFormLayout."""

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            pass

        w = MyForm()
        qt.track(w)

        assert_that(w.layout()).is_instance_of(QFormLayout)

    def test_form_label_creates_row(self, qt: QtDriver) -> None:
        """form_label parameter should create a labeled row."""

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            name: QLineEdit = make(QLineEdit, form_label="Full Name")

        w = MyForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Should have one row
        assert_that(layout.rowCount()).is_equal_to(1)

        # Get the label for row 0
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        label_widget = label_item.widget()
        assert isinstance(label_widget, QLabel)
        assert_that(label_widget.text()).is_equal_to("Full Name")

        # Get the field for row 0
        field_item = layout.itemAt(0, QFormLayout.ItemRole.FieldRole)
        assert field_item is not None
        assert_that(field_item.widget()).is_same_as(w.name)

    def test_form_multiple_rows_in_order(self, qt: QtDriver) -> None:
        """Multiple fields should create rows in declaration order."""

        @widget(layout="form")
        class PersonForm(QWidget, Widget):
            name: QLineEdit = make(QLineEdit, form_label="Name")
            email: QLineEdit = make(QLineEdit, form_label="Email")
            age: QSpinBox = make(QSpinBox, form_label="Age")

        w = PersonForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        assert_that(layout.rowCount()).is_equal_to(3)

        # Check each row's label
        labels: list[str] = []
        for row in range(3):
            label_item = layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            assert label_item is not None
            label_widget = label_item.widget()
            assert isinstance(label_widget, QLabel)
            labels.append(label_widget.text())

        assert_that(labels).is_equal_to(["Name", "Email", "Age"])

        # Check each row's field widget
        field_item_0 = layout.itemAt(0, QFormLayout.ItemRole.FieldRole)
        field_item_1 = layout.itemAt(1, QFormLayout.ItemRole.FieldRole)
        field_item_2 = layout.itemAt(2, QFormLayout.ItemRole.FieldRole)
        assert field_item_0 is not None and field_item_1 is not None and field_item_2 is not None
        assert_that(field_item_0.widget()).is_same_as(w.name)
        assert_that(field_item_1.widget()).is_same_as(w.email)
        assert_that(field_item_2.widget()).is_same_as(w.age)

    def test_form_adds_form_class(self, qt: QtDriver) -> None:
        """Form layout should auto-add 'form' class for styling."""

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            pass

        w = MyForm()
        qt.track(w)

        class_prop = w.property("class")
        assert_that(class_prop).contains("form")

    def test_form_preserves_existing_classes(self, qt: QtDriver) -> None:
        """Form layout should preserve existing classes when adding 'form'."""

        @widget(layout="form", classes=["card", "shadow"])
        class MyForm(QWidget, Widget):
            pass

        w = MyForm()
        qt.track(w)

        class_prop = w.property("class")
        assert_that(class_prop).contains("card")
        assert_that(class_prop).contains("shadow")
        assert_that(class_prop).contains("form")

    def test_form_without_label_uses_empty_string(self, qt: QtDriver) -> None:
        """Widget without form_label should still be added to form."""

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            name: QLineEdit = make(QLineEdit)  # No form_label

        w = MyForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Should still have one row
        assert_that(layout.rowCount()).is_equal_to(1)

        # Field should be present (Qt may not create a label widget for empty string)
        field_item = layout.itemAt(0, QFormLayout.ItemRole.FieldRole)
        assert field_item is not None
        assert_that(field_item.widget()).is_same_as(w.name)

    def test_form_includes_single_underscore_fields(self, qt: QtDriver) -> None:
        """Single underscore fields ARE added to form layout."""

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            name: QLineEdit = make(QLineEdit, form_label="Name")
            _helper: QLabel = make(QLabel, "Helper")

        w = MyForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Both fields should be in the layout
        assert_that(layout.rowCount()).is_equal_to(2)

    def test_form_skips_excluded_fields(self, qt: QtDriver) -> None:
        """Fields like _foo_ should NOT be added to form layout."""

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            name: QLineEdit = make(QLineEdit, form_label="Name")
            _excluded_: QLabel = make(QLabel, "Excluded")

        w = MyForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Only one row (excluded field not added)
        assert_that(layout.rowCount()).is_equal_to(1)
