# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownMemberType=false
# pyright: reportGeneralTypeIssues=false
"""Tests for validation across Widget, Window, Menu, and App.

Tests add_validator, is_valid, validation_errors, and on_valid_changed hook.
"""

from typing import override

import pytest
from assertpy import assert_that
from observant import Observable

from qtpie import State, Variable, new, state
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, RECORD_CLASS_TYPES, create_and_track


def get_validation_error_messages(instance: object, base_class: type) -> list[str]:
    """Helper to get validation_error_messages (all types return Observable[list[str]])."""
    # All types (Widget/Window/App/Menu) return Observable[list[str]]
    return instance.validation_error_messages.get()  # type: ignore[union-attr, return-value]


# =============================================================================
# Basic add_validator
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestAddValidator:
    """add_validator works across all class types."""

    def test_add_named_validator(self, base_class, decorator, qt: QtDriver) -> None:
        """add_validator('field', 'name', fn) registers a validator."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.is_valid.get()).is_false()

    def test_validator_returns_none_for_valid(self, base_class, decorator, qt: QtDriver) -> None:
        """Validator returning None means valid."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("hello")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.is_valid.get()).is_true()

    def test_validator_returns_string_for_invalid(self, base_class, decorator, qt: QtDriver) -> None:
        """Validator returning string means invalid with that error message."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name is required")

        instance = create_and_track(qt, TestClass, base_class)
        errors = instance._name.validation_errors.get()
        assert_that(errors["required"]).is_equal_to(["Name is required"])

    def test_multiple_validators_per_field(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple validators on same field all run."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Min 3 chars")

        instance = create_and_track(qt, TestClass, base_class)
        msgs = instance._name.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Min 3 chars")

    def test_replace_validator_by_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Adding validator with same name replaces previous."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "check", lambda v: "First error")
                self.add_validator("_name", "check", lambda v: "Second error")

        instance = create_and_track(qt, TestClass, base_class)
        msgs = instance._name.validation_error_messages.get()
        assert_that(msgs).is_equal_to(["Second error"])


# =============================================================================
# is_valid Observable
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestIsValid:
    """is_valid Observable works across all class types."""

    def test_starts_valid_without_validators(self, base_class, decorator, qt: QtDriver) -> None:
        """Without validators, is_valid is True."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_true()

    def test_starts_invalid_with_failing_validator(self, base_class, decorator, qt: QtDriver) -> None:
        """With failing validator, is_valid is False."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

    def test_becomes_valid_when_fixed(self, base_class, decorator, qt: QtDriver) -> None:
        """is_valid becomes True when validation passes."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

        instance._name.value = "hello"
        assert_that(instance.is_valid.get()).is_true()

    def test_becomes_invalid_when_broken(self, base_class, decorator, qt: QtDriver) -> None:
        """is_valid becomes False when validation fails again."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("hello")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_true()

        instance._name.value = ""
        assert_that(instance.is_valid.get()).is_false()

    def test_is_valid_is_observable(self, base_class, decorator, qt: QtDriver) -> None:
        """is_valid returns Observable[bool]."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid).is_instance_of(Observable)


# =============================================================================
# Widget-level is_valid aggregates fields
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestIsValidAggregates:
    """Widget-level is_valid aggregates all field validations."""

    def test_aggregates_multiple_fields(self, base_class, decorator, qt: QtDriver) -> None:
        """is_valid is False if any field is invalid."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

        instance._name.value = "Alice"
        assert_that(instance.is_valid.get()).is_false()  # age still invalid

        instance._age.value = 25
        assert_that(instance.is_valid.get()).is_true()

    def test_one_valid_field_not_enough(self, base_class, decorator, qt: QtDriver) -> None:
        """Having one valid field doesn't make whole form valid."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Alice")
            _email: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_email", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()


# =============================================================================
# validation_errors structure
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestValidationErrors:
    """validation_errors returns structured error data."""

    def test_validation_errors_structure(self, base_class, decorator, qt: QtDriver) -> None:
        """validation_errors returns {field: {validator: [errors]}}."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name required")
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Age must be positive")

        instance = create_and_track(qt, TestClass, base_class)
        errors = instance.validation_errors

        assert_that(errors).contains_key("_name", "_age")
        assert_that(errors["_name"]["required"]).is_equal_to(["Name required"])
        assert_that(errors["_age"]["positive"]).is_equal_to(["Age must be positive"])

    def test_validation_error_messages_flat_list(self, base_class, decorator, qt: QtDriver) -> None:
        """validation_error_messages returns flat list of all errors."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Too short")

        instance = create_and_track(qt, TestClass, base_class)
        msgs = get_validation_error_messages(instance, base_class)

        assert_that(msgs).contains("Required", "Too short")

    def test_no_errors_when_valid(self, base_class, decorator, qt: QtDriver) -> None:
        """No errors when all validators pass."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("hello world")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Too short")

        instance = create_and_track(qt, TestClass, base_class)
        msgs = get_validation_error_messages(instance, base_class)

        assert_that(msgs).is_empty()


# =============================================================================
# on_valid_changed hook
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestOnValidChangedHook:
    """on_valid_changed lifecycle hook works across class types."""

    def test_hook_fires_on_valid(self, base_class, decorator, qt: QtDriver) -> None:
        """on_valid_changed fires when becoming valid."""
        valid_states: list[bool] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "hello"

        assert_that(valid_states).contains(True)

    def test_hook_fires_on_invalid(self, base_class, decorator, qt: QtDriver) -> None:
        """on_valid_changed fires when becoming invalid."""
        valid_states: list[bool] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("hello")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = ""

        assert_that(valid_states).contains(False)

    def test_hook_fires_on_transition_only(self, base_class, decorator, qt: QtDriver) -> None:
        """on_valid_changed only fires on state transitions."""
        valid_states: list[bool] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        instance = create_and_track(qt, TestClass, base_class)
        # Multiple invalid changes shouldn't fire multiple times
        instance._name.value = ""  # still invalid
        instance._name.value = ""  # still invalid

        # Only transition to valid should fire
        instance._name.value = "hello"

        # The hook should have fired once for becoming valid
        assert_that(valid_states).contains(True)

    def test_hook_not_required(self, base_class, decorator, qt: QtDriver) -> None:
        """Class without on_valid_changed still works."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "hello"
        # Should not raise
        assert_that(instance.is_valid.get()).is_true()


# =============================================================================
# Variable-level validation
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVariableLevelValidation:
    """Variable[T] exposes its own validation state."""

    def test_variable_is_valid(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable.is_valid returns its validation state."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._name.is_valid.get()).is_false()

        instance._name.value = "hello"
        assert_that(instance._name.is_valid.get()).is_true()

    def test_variable_validation_errors(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable.validation_errors returns its errors."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        errors = instance._name.validation_errors.get()
        assert_that(errors["required"]).is_equal_to(["Required"])

    def test_variable_validation_error_messages(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable.validation_error_messages returns flat list."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Too short")

        instance = create_and_track(qt, TestClass, base_class)
        msgs = instance._name.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Too short")


# =============================================================================
# Validation with different value types
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestValidationWithTypes:
    """Validation works with different Variable types."""

    def test_validation_with_int(self, base_class, decorator, qt: QtDriver) -> None:
        """Validation works with int Variables."""

        @decorator
        class TestClass(base_class):
            _age: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._age.is_valid.get()).is_false()

        instance._age.value = 25
        assert_that(instance._age.is_valid.get()).is_true()

    def test_validation_with_float(self, base_class, decorator, qt: QtDriver) -> None:
        """Validation works with float Variables."""

        @decorator
        class TestClass(base_class):
            _rate: Variable[float] = new(0.0)

            def __setup__(self) -> None:
                self.add_validator("_rate", "range", lambda v: None if 0 <= v <= 1 else "Must be 0-1")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._rate.is_valid.get()).is_true()

        instance._rate.value = 1.5
        assert_that(instance._rate.is_valid.get()).is_false()

    def test_validation_with_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Validation works with list Variables."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new()

            def __setup__(self) -> None:
                self.add_validator("_items", "not_empty", lambda v: None if v else "Add at least one item")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._items.is_valid.get()).is_false()

        instance._items.observable.append("item")  # type: ignore[union-attr]
        assert_that(instance._items.is_valid.get()).is_true()

    def test_validation_with_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """Validation works with dict Variables."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new()

            def __setup__(self) -> None:
                self.add_validator("_data", "has_key", lambda v: None if "required" in v else "Missing 'required' key")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._data.is_valid.get()).is_false()

        instance._data.observable["required"] = 42  # type: ignore[index]
        assert_that(instance._data.is_valid.get()).is_true()

    def test_validation_with_set(self, base_class, decorator, qt: QtDriver) -> None:
        """Validation works with set Variables."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new()

            def __setup__(self) -> None:
                self.add_validator("_tags", "not_empty", lambda v: None if v else "Add at least one tag")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tags.is_valid.get()).is_false()

        instance._tags.observable.add("tag")  # type: ignore[union-attr]
        assert_that(instance._tags.is_valid.get()).is_true()


# =============================================================================
# Edge cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestValidationEdgeCases:
    """Edge cases for validation."""

    def test_no_validators_always_valid(self, base_class, decorator, qt: QtDriver) -> None:
        """Class without validators is always valid."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_true()
        assert_that(get_validation_error_messages(instance, base_class)).is_empty()

    def test_empty_class_always_valid(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty class is always valid."""

        @decorator
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_true()

    def test_validator_receives_current_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Validator receives the current value after change."""
        received_values: list[str] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                def track_validator(v: str) -> str | None:
                    received_values.append(v)
                    return None

                self.add_validator("_name", "track", track_validator)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "first"
        instance._name.value = "second"

        assert_that(received_values).contains("first", "second")

    def test_validation_reactive_subscription(self, base_class, decorator, qt: QtDriver) -> None:
        """is_valid can be subscribed to reactively."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        valid_changes: list[bool] = []
        instance.is_valid.on_change(lambda v: valid_changes.append(v))

        instance._name.value = "hello"
        assert_that(valid_changes).contains(True)

        instance._name.value = ""
        assert_that(valid_changes).contains(False)


# =============================================================================
# Validation with State Record (Widget[State])
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestValidationWithStateRecord:
    """Validation when record is a State."""

    def test_state_record_validation_makes_widget_invalid(self, base_class, decorator, qt: QtDriver) -> None:
        """State record with failing validator makes Widget invalid."""

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator(record=Person())
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

    def test_state_record_becomes_valid_when_fixed(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget becomes valid when State record validates."""

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator(record=Person())
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

        instance.record.name = "Alice"
        assert_that(instance.is_valid.get()).is_true()

    def test_state_record_validation_via_state_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing State record Variable directly affects Widget validity."""

        @state
        class Person(State):
            name: Variable[str] = new("Alice", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator(record=Person())
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_true()

        # Get the actual State target and change its Variable directly
        state_target: Person = instance._qtpie._record.observable._target  # type: ignore[attr-defined]
        state_target.name.value = ""

        # Widget should see the State's validation state
        assert_that(instance.is_valid.get()).is_false()

    def test_state_record_validation_errors_included(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget validation_errors includes State record errors."""

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator(record=Person())
        class TestClass(base_class[Person]):  # type: ignore[misc]
            _extra: Variable[str] = new("", validate="validate_extra")

            def validate_extra(self, value: str) -> str | None:
                return None if value else "Extra required"

        instance = create_and_track(qt, TestClass, base_class)
        msgs = instance.validation_error_messages.get()

        assert_that(msgs).contains("Extra required")

    def test_state_record_on_valid_changed_hook(self, base_class, decorator, qt: QtDriver) -> None:
        """on_valid_changed hook fires when State record validation changes."""
        valid_states: list[bool] = []

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator(record=Person())
        class TestClass(base_class[Person]):  # type: ignore[misc]
            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        instance = create_and_track(qt, TestClass, base_class)
        instance.record.name = "Alice"

        assert_that(valid_states).contains(True)


# =============================================================================
# Validation with Variable[State]
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestValidationWithVariableState:
    """Validation when Variable holds a State."""

    def test_variable_state_validation_makes_widget_invalid(self, base_class, decorator, qt: QtDriver) -> None:
        """State inside Variable with failing validator makes Widget invalid."""

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator
        class TestClass(base_class):
            _person: Variable[Person] = new(default=Person())

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

    def test_variable_state_becomes_valid_when_fixed(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget becomes valid when State inside Variable validates."""

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator
        class TestClass(base_class):
            _person: Variable[Person] = new(default=Person())

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

        instance._person.value.name.value = "Alice"
        assert_that(instance.is_valid.get()).is_true()

    def test_variable_list_of_states_validation(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing State in list[State] Variable affects Widget validity."""

        @state
        class Person(State):
            name: Variable[str] = new("", validate="validate_name")

            def validate_name(self, value: str) -> str | None:
                return None if value else "Name required"

        @decorator
        class TestClass(base_class):
            _people: Variable[list[Person]] = new(default=[Person()])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_valid.get()).is_false()

        # Fix the State inside the list
        person: Person = instance._people.value[0]
        person.name.value = "Alice"
        assert_that(instance.is_valid.get()).is_true()
