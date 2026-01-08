# pyright: reportPrivateUsage=false, reportUnknownMemberType=false, reportUnknownLambdaType=false
"""Tests for QtPie validation support."""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QPushButton

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


class TestIsValidObservable:
    """Test that Widget.is_valid is Observable[bool] for reactive bindings."""

    def test_is_valid_is_observable(self, qt: QtDriver) -> None:
        """Widget.is_valid should return Observable[bool]."""
        from observant import Observable

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = qt.track(TestWidget())
        # is_valid should be an Observable, not a plain bool
        assert_that(w.is_valid).is_instance_of(Observable)
        assert_that(w.is_valid.get()).is_false()

    def test_is_valid_reactive_updates(self, qt: QtDriver) -> None:
        """Widget.is_valid Observable should update when validity changes."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = qt.track(TestWidget())
        validity_changes: list[bool] = []
        w.is_valid.on_change(lambda v: validity_changes.append(v))

        # Initially invalid
        assert_that(w.is_valid.get()).is_false()

        # Become valid
        w._name.value = "hello"
        assert_that(w.is_valid.get()).is_true()
        assert_that(validity_changes).contains(True)

        # Become invalid again
        w._name.value = ""
        assert_that(w.is_valid.get()).is_false()
        assert_that(validity_changes).contains(False)

    def test_is_valid_in_binding(self, qt: QtDriver) -> None:
        """Widget.is_valid can be used in enabled= bindings."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")
            _submit: QPushButton = new("Submit", enabled="{is_valid.get()}")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = qt.track(TestWidget())
        # Initially invalid - button should be disabled
        assert_that(w._submit.isEnabled()).is_false()

        # Become valid - button should enable
        w._name.value = "hello"
        assert_that(w._submit.isEnabled()).is_true()

        # Become invalid - button should disable
        w._name.value = ""
        assert_that(w._submit.isEnabled()).is_false()

    def test_is_valid_without_validators_is_observable(self, qt: QtDriver) -> None:
        """Widget without validators still returns Observable[bool] for is_valid."""
        from observant import Observable

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(TestWidget())
        assert_that(w.is_valid).is_instance_of(Observable)
        assert_that(w.is_valid.get()).is_true()


class TestValidateParameter:
    """Test validate= parameter on Variable fields."""

    def test_validate_single_method_name(self, qt: QtDriver) -> None:
        """validate='method_name' registers a single validator."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Required"

        w = qt.track(TestWidget())
        assert_that(w._name.is_valid.get()).is_false()

        w._name.value = "hello"
        assert_that(w._name.is_valid.get()).is_true()

    def test_validate_list_of_method_names(self, qt: QtDriver) -> None:
        """validate=['m1', 'm2'] registers multiple validators."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("", validate=["validate_required", "validate_length"])

            def validate_required(self, value: str) -> str | None:
                return None if value else "Required"

            def validate_length(self, value: str) -> str | None:
                return None if len(value) >= 3 else "Too short"

        w = qt.track(TestWidget())
        msgs = w._name.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Too short")

        w._name.value = "ab"
        msgs = w._name.validation_error_messages.get()
        assert_that(msgs).is_equal_to(["Too short"])

        w._name.value = "abc"
        assert_that(w._name.is_valid.get()).is_true()

    def test_validate_with_callable(self, qt: QtDriver) -> None:
        """validate=callable registers a callable as validator."""

        def check_not_empty(value: str) -> str | None:
            return None if value else "Cannot be empty"

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("", validate=check_not_empty)

        w = qt.track(TestWidget())
        assert_that(w._name.is_valid.get()).is_false()
        assert_that(w._name.validation_error_messages.get()).contains("Cannot be empty")

    def test_validate_with_tuple_explicit_name(self, qt: QtDriver) -> None:
        """validate=[('name', 'method')] uses explicit validator name."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("", validate=[("custom_name", "validate_required")])

            def validate_required(self, value: str) -> str | None:
                return None if value else "Required"

        w = qt.track(TestWidget())
        errors = w._name.validation_errors.get()
        assert_that(errors).contains_key("custom_name")

    def test_validate_with_tuple_callable(self, qt: QtDriver) -> None:
        """validate=[('name', callable)] uses explicit name with callable."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("", validate=[("my_validator", lambda v: None if v else "Empty")])

        w = qt.track(TestWidget())
        errors = w._name.validation_errors.get()
        assert_that(errors).contains_key("my_validator")
        assert_that(errors["my_validator"]).is_equal_to(["Empty"])

    def test_validate_mixed_formats(self, qt: QtDriver) -> None:
        """validate= supports mixing different formats."""

        def external_check(value: str) -> str | None:
            return None if value.isalpha() else "Letters only"

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new(
                "",
                validate=[
                    "validate_required",
                    external_check,
                    ("length_check", "validate_length"),
                ],
            )

            def validate_required(self, value: str) -> str | None:
                return None if value else "Required"

            def validate_length(self, value: str) -> str | None:
                return None if len(value) >= 3 else "Too short"

        w = qt.track(TestWidget())
        msgs = w._name.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Letters only", "Too short")

    def test_validate_runs_before_setup(self, qt: QtDriver) -> None:
        """Validators are registered before __setup__ runs."""
        setup_validity: list[bool] = []

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Required"

            def __setup__(self) -> None:
                # Validator should already be active
                setup_validity.append(self._name.is_valid.get())

        qt.track(TestWidget())
        assert_that(setup_validity).is_equal_to([False])

    def test_validate_with_widget_type(self, qt: QtDriver) -> None:
        """validate= works with Variable[T, W] syntax."""
        from qtpy.QtWidgets import QLineEdit

        @widget
        class TestWidget(Widget):
            name: Variable[str, QLineEdit] = new("", validate="check_name")

            def check_name(self, value: str) -> str | None:
                return None if value else "Name required"

        w = qt.track(TestWidget())
        assert_that(w.name.is_valid.get()).is_false()

        w.name.widget.setText("Alice")
        assert_that(w.name.is_valid.get()).is_true()
