"""Tests for Widget[T] Observant integration (validation, dirty, undo, save/load)."""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox, QWidget

from qtpie import Widget, make, widget
from qtpie_test import QtDriver


@dataclass
class User:
    name: str = ""
    age: int = 0
    email: str = ""


class TestWidgetFormatBinding:
    """Tests for format string binding with Widget[T] model fields."""

    def test_format_binding_with_model_fields(self, qt: QtDriver) -> None:
        """bind='Name: {name}' should work with Widget[T] model fields."""

        @widget
        class UserDisplay(QWidget, Widget[User]):
            name_edit: QLineEdit = make(QLineEdit, bind="name")  # Explicit bind
            label: QLabel = make(QLabel, bind="Name: {name}")

        w = UserDisplay()
        qt.track(w)

        # Initial value (empty name)
        assert_that(w.label.text()).is_equal_to("Name: ")

        # Change via input - triggers two-way binding to proxy.name
        w.name_edit.setText("Alice")
        assert_that(w.label.text()).is_equal_to("Name: Alice")

    def test_format_binding_multiple_model_fields(self, qt: QtDriver) -> None:
        """bind='{name}, age {age}' should work with multiple model fields."""

        @widget
        class UserDisplay(QWidget, Widget[User]):
            name_edit: QLineEdit = make(QLineEdit, bind="name")  # Explicit bind
            age_spin: QSpinBox = make(QSpinBox, bind="age")  # Explicit bind
            label: QLabel = make(QLabel, bind="{name}, age {age}")

        w = UserDisplay()
        qt.track(w)

        w.name_edit.setText("Bob")
        w.age_spin.setValue(25)

        assert_that(w.label.text()).is_equal_to("Bob, age 25")

    def test_format_binding_same_name_as_widget(self, qt: QtDriver) -> None:
        """bind='{name}' should use model.name even when widget is also named 'name'."""

        @widget
        class UserDisplay(QWidget, Widget[User]):
            # Widget field name matches model field name
            name: QLineEdit = make(QLineEdit, bind="name")
            age: QSpinBox = make(QSpinBox, bind="age")
            info: QLabel = make(QLabel, bind="Name: {name}, Age: {age}")

        w = UserDisplay()
        qt.track(w)

        # Initially empty
        assert_that(w.info.text()).is_equal_to("Name: , Age: 0")

        # Change via widgets
        w.name.setText("Alice")
        w.age.setValue(25)

        # Format binding should use model values, not the QLineEdit widgets
        assert_that(w.info.text()).is_equal_to("Name: Alice, Age: 25")


class TestWidgetValidation:
    """Tests for Widget[T] validation delegate methods."""

    def test_add_validator_basic(self, qt: QtDriver) -> None:
        """add_validator should add a validation rule to a field."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        # Add validator
        w.add_validator("name", lambda v: "Required" if not v else None)

        # Initially invalid (empty name)
        assert_that(w.is_valid().get()).is_false()

        # Set valid value
        w.name.setText("Alice")
        assert_that(w.is_valid().get()).is_true()

    def test_validation_for_returns_errors(self, qt: QtDriver) -> None:
        """validation_for should return errors for a specific field."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = UserEditor()
        qt.track(w)

        w.add_validator("name", lambda v: "Name required" if not v else None)
        w.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

        # Check individual field errors
        name_errors = w.validation_for("name").get()
        age_errors = w.validation_for("age").get()

        assert_that(name_errors).contains("Name required")
        assert_that(age_errors).contains("Must be 18+")

        # Fix name
        w.name.setText("Bob")
        assert_that(w.validation_for("name").get()).is_empty()

    def test_validation_errors_returns_all(self, qt: QtDriver) -> None:
        """validation_errors should return all field errors as an observable dict."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)
            email: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        w.add_validator("name", lambda v: "Required" if not v else None)
        w.add_validator("email", lambda v: "Invalid" if "@" not in v else None)

        # validation_errors returns an ObservableDict - access individual field errors
        name_errors = w.validation_errors().get("name", [])
        email_errors = w.validation_errors().get("email", [])

        assert_that(name_errors).contains("Required")
        assert_that(email_errors).contains("Invalid")


class TestWidgetDirtyTracking:
    """Tests for Widget[T] dirty tracking delegate methods."""

    def test_is_dirty_initially_false(self, qt: QtDriver) -> None:
        """is_dirty should be False initially."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        assert_that(w.is_dirty()).is_false()

    def test_is_dirty_after_change(self, qt: QtDriver) -> None:
        """is_dirty should be True after a field changes."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        w.name.setText("Alice")
        assert_that(w.is_dirty()).is_true()

    def test_dirty_fields_lists_modified(self, qt: QtDriver) -> None:
        """dirty_fields should list modified field names."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = UserEditor()
        qt.track(w)

        w.name.setText("Alice")
        assert_that(w.dirty_fields()).contains("name")
        assert_that(w.dirty_fields()).does_not_contain("age")

    def test_reset_dirty_clears_state(self, qt: QtDriver) -> None:
        """reset_dirty should mark all fields as clean."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        w.name.setText("Alice")
        assert_that(w.is_dirty()).is_true()

        w.reset_dirty()
        assert_that(w.is_dirty()).is_false()


class TestWidgetUndo:
    """Tests for Widget[T] undo/redo delegate methods."""

    def test_undo_reverts_change(self, qt: QtDriver) -> None:
        """undo should revert a field to its previous value."""

        @widget(undo=True)
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        # Make a change
        w.name.setText("Alice")
        assert_that(w.proxy.observable(str, "name").get()).is_equal_to("Alice")

        # Undo
        w.undo("name")
        assert_that(w.proxy.observable(str, "name").get()).is_equal_to("")

    def test_redo_restores_change(self, qt: QtDriver) -> None:
        """redo should restore a previously undone change."""

        @widget(undo=True)
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        w.name.setText("Alice")
        w.undo("name")
        assert_that(w.proxy.observable(str, "name").get()).is_equal_to("")

        w.redo("name")
        assert_that(w.proxy.observable(str, "name").get()).is_equal_to("Alice")

    def test_can_undo_returns_availability(self, qt: QtDriver) -> None:
        """can_undo should indicate whether undo is available."""

        @widget(undo=True)
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        # No undo initially
        assert_that(w.can_undo("name")).is_false()

        # After change, undo available
        w.name.setText("Alice")
        assert_that(w.can_undo("name")).is_true()

        # After undo, no more undo
        w.undo("name")
        assert_that(w.can_undo("name")).is_false()

    def test_can_redo_returns_availability(self, qt: QtDriver) -> None:
        """can_redo should indicate whether redo is available."""

        @widget(undo=True)
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        # No redo initially
        assert_that(w.can_redo("name")).is_false()

        # After undo, redo available
        w.name.setText("Alice")
        w.undo("name")
        assert_that(w.can_redo("name")).is_true()


class TestWidgetSaveLoad:
    """Tests for Widget[T] save/load delegate methods."""

    def test_save_to_copies_to_model(self, qt: QtDriver) -> None:
        """save_to should copy proxy values to the target model."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = UserEditor()
        qt.track(w)

        w.name.setText("Alice")
        w.age.setValue(30)

        # Save to original model
        w.save_to(w.model)

        assert_that(w.model.name).is_equal_to("Alice")
        assert_that(w.model.age).is_equal_to(30)

    def test_save_to_different_instance(self, qt: QtDriver) -> None:
        """save_to should copy values to a different model instance."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)

        w = UserEditor()
        qt.track(w)

        w.name.setText("Bob")

        # Create a new user and save to it
        new_user = User(name="Original")
        w.save_to(new_user)

        # New user gets the proxy values
        assert_that(new_user.name).is_equal_to("Bob")

    def test_load_dict_updates_proxy(self, qt: QtDriver) -> None:
        """load_dict should update proxy values from a dictionary."""

        @widget
        class UserEditor(QWidget, Widget[User]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = UserEditor()
        qt.track(w)

        w.load_dict({"name": "Charlie", "age": 25})

        assert_that(w.name.text()).is_equal_to("Charlie")
        assert_that(w.age.value()).is_equal_to(25)
