# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Tests for QtPie validation support."""

from dataclasses import dataclass

from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class Person:
    """Test model."""

    name: str = ""
    age: int = 0


class TestVariableValidation:
    """Test Variable[T] validation forwarding."""

    def test_variable_forwards_add_validator(self, qt: QtDriver) -> None:
        """Variable forwards add_validator to wrapper."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(TestWidget())
        w._name.add_validator("required", lambda v: None if v else "Required")

        assert_that(w._name.is_valid.get()).is_false()

    def test_variable_forwards_is_valid(self, qt: QtDriver) -> None:
        """Variable.is_valid returns Observable[bool]."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("hello")

        w = qt.track(TestWidget())
        w._name.add_validator("required", lambda v: None if v else "Required")

        assert_that(w._name.is_valid.get()).is_true()

    def test_variable_forwards_validation_errors(self, qt: QtDriver) -> None:
        """Variable.validation_errors returns Observable[dict]."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(TestWidget())
        w._name.add_validator("required", lambda v: None if v else "Required")

        errors = w._name.validation_errors.get()
        assert_that(errors).contains_key("required")
        assert_that(errors["required"]).is_equal_to(["Required"])

    def test_variable_forwards_validation_error_messages(self, qt: QtDriver) -> None:
        """Variable.validation_error_messages returns flat list."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(TestWidget())
        w._name.add_validator("required", lambda v: None if v else "Required")
        w._name.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

        msgs = w._name.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Too short")


class TestWidgetValidation:
    """Test Widget validation API."""

    def test_widget_add_validator(self, qt: QtDriver) -> None:
        """Widget.add_validator adds validator to field."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = qt.track(TestWidget())
        assert_that(w._name.is_valid.get()).is_false()

    def test_widget_is_valid_aggregates(self, qt: QtDriver) -> None:
        """Widget.is_valid aggregates from all fields."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

        w = qt.track(TestWidget())
        assert_that(w.is_valid).is_false()

        w._name.value = "Alice"
        assert_that(w.is_valid).is_false()  # still invalid (age)

        w._age.value = 25
        assert_that(w.is_valid).is_true()

    def test_widget_validation_errors_nested_dict(self, qt: QtDriver) -> None:
        """Widget.validation_errors returns {field: {validator: [errors]}}."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

        w = qt.track(TestWidget())
        errors = w.validation_errors

        assert_that(errors).contains_key("_name", "_age")
        assert_that(errors["_name"]["required"]).is_equal_to(["Required"])
        assert_that(errors["_age"]["positive"]).is_equal_to(["Must be positive"])

    def test_widget_validation_error_messages_flat(self, qt: QtDriver) -> None:
        """Widget.validation_error_messages returns flat list."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Too short")

        w = qt.track(TestWidget())
        msgs = w.validation_error_messages

        assert_that(msgs).contains("Required", "Too short")

    def test_on_valid_changed_hook(self, qt: QtDriver) -> None:
        """on_valid_changed fires when validity changes."""
        valid_states: list[bool] = []

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        w = qt.track(TestWidget())
        # Initially invalid, but hook fires on transition only

        w._name.value = "hello"
        assert_that(valid_states).contains(True)

        w._name.value = ""
        assert_that(valid_states).contains(False)

    def test_record_field_validation(self, qt: QtDriver) -> None:
        """Can add validators to record fields."""

        @widget
        class PersonEditor(Widget[Person]):
            def __setup__(self) -> None:
                self.add_validator("name", "required", lambda v: None if v else "Name required")

        w = qt.track(PersonEditor())
        assert_that(w.is_valid).is_false()

        w.record.name = "Alice"
        assert_that(w.is_valid).is_true()

    def test_widget_valid_without_validators(self, qt: QtDriver) -> None:
        """Widget without validators is always valid."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")
            _label: QLabel = new("Hello")

        w = qt.track(TestWidget())
        assert_that(w.is_valid).is_true()


class TestValidationWithUI:
    """Test validation with UI elements."""

    def test_enable_button_on_valid(self, qt: QtDriver) -> None:
        """Use validation to enable/disable submit button."""

        @widget
        class LoginForm(Widget):
            _username: Variable[str] = new("")
            _password: Variable[str] = new("")
            _submit: QPushButton = new("Login")

            def __setup__(self) -> None:
                self.add_validator("_username", "required", lambda v: None if v else "Username required")
                self.add_validator("_password", "required", lambda v: None if v else "Password required")
                self._submit.setEnabled(False)

            def on_valid_changed(self, is_valid: bool) -> None:
                self._submit.setEnabled(is_valid)

        w = qt.track(LoginForm())
        assert_that(w._submit.isEnabled()).is_false()

        w._username.value = "user"
        assert_that(w._submit.isEnabled()).is_false()

        w._password.value = "pass"
        assert_that(w._submit.isEnabled()).is_true()

        w._username.value = ""
        assert_that(w._submit.isEnabled()).is_false()
