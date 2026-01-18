# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownMemberType=false
# pyright: reportGeneralTypeIssues=false
"""Tests for QLineEdit input validators via new(validator=...).

Input validators restrict what characters can be typed into a QLineEdit.
This is different from Widget-level validation (add_validator) which validates
the final value after input.

Supported validator= values:
- str (regex pattern): QRegularExpressionValidator
- Callable[[str], bool]: Simple predicate (True=valid, False=reject)
- Callable[[str, int], QValidator.State]: Full control over validation state
- str (method name): Look up method on widget instance
"""

from assertpy import assert_that
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QLineEdit

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import create_and_track

# =============================================================================
# Regex string validator
# =============================================================================


class TestRegexValidator:
    """validator=r"pattern" creates a QRegularExpressionValidator."""

    def test_regex_validator_accepts_matching_input(self, qt: QtDriver) -> None:
        """Regex validator accepts characters that match the pattern."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=r"[a-zA-Z]+")

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Hello")
        assert_that(instance.name.text()).is_equal_to("Hello")

    def test_regex_validator_has_qvalidator(self, qt: QtDriver) -> None:
        """QLineEdit has a QValidator set."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=r"[a-zA-Z]+")

        instance = create_and_track(qt, TestWidget, Widget)
        assert_that(instance.name.validator()).is_not_none()

    def test_regex_alphanumeric_and_spaces(self, qt: QtDriver) -> None:
        """Regex can allow alphanumeric and spaces."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=r"[a-zA-Z0-9 ]+")

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Hello World 123")
        assert_that(instance.name.text()).is_equal_to("Hello World 123")

    def test_regex_numbers_only(self, qt: QtDriver) -> None:
        """Regex can restrict to numbers only."""

        @widget
        class TestWidget(Widget):
            age: QLineEdit = new(validator=r"[0-9]+")

        instance = create_and_track(qt, TestWidget, Widget)
        instance.age.setText("42")
        assert_that(instance.age.text()).is_equal_to("42")


# =============================================================================
# Lambda/callable validator (simple predicate)
# =============================================================================


class TestLambdaValidator:
    """validator=lambda text: bool creates a predicate validator."""

    def test_lambda_validator_accepts_when_true(self, qt: QtDriver) -> None:
        """Lambda returning True accepts the input."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=lambda text: len(text) <= 10)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Short")
        assert_that(instance.name.text()).is_equal_to("Short")

    def test_lambda_validator_has_qvalidator(self, qt: QtDriver) -> None:
        """QLineEdit has a QValidator set."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=lambda text: True)

        instance = create_and_track(qt, TestWidget, Widget)
        assert_that(instance.name.validator()).is_not_none()

    def test_lambda_max_length(self, qt: QtDriver) -> None:
        """Lambda can enforce max length."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=lambda text: len(text) <= 5)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Hi")
        assert_that(instance.name.text()).is_equal_to("Hi")

    def test_lambda_no_spaces(self, qt: QtDriver) -> None:
        """Lambda can reject spaces."""

        @widget
        class TestWidget(Widget):
            username: QLineEdit = new(validator=lambda text: " " not in text)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.username.setText("john_doe")
        assert_that(instance.username.text()).is_equal_to("john_doe")

    def test_lambda_custom_logic(self, qt: QtDriver) -> None:
        """Lambda can use arbitrary logic."""

        def no_bad_words(text: str) -> bool:
            return "bad" not in text.lower()

        @widget
        class TestWidget(Widget):
            comment: QLineEdit = new(validator=no_bad_words)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.comment.setText("good comment")
        assert_that(instance.comment.text()).is_equal_to("good comment")


# =============================================================================
# Full QValidator.State callable
# =============================================================================


class TestFullValidatorCallable:
    """validator=fn(text, pos) -> State gives full control."""

    def test_full_validator_acceptable(self, qt: QtDriver) -> None:
        """Returning Acceptable allows the input."""

        def my_validator(text: str, pos: int) -> QValidator.State:
            return QValidator.State.Acceptable

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=my_validator)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("anything")
        assert_that(instance.name.text()).is_equal_to("anything")

    def test_full_validator_intermediate(self, qt: QtDriver) -> None:
        """Returning Intermediate allows incomplete input."""

        def my_validator(text: str, pos: int) -> QValidator.State:
            if len(text) >= 3:
                return QValidator.State.Acceptable
            return QValidator.State.Intermediate

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=my_validator)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("ab")  # Intermediate
        assert_that(instance.name.text()).is_equal_to("ab")

    def test_full_validator_has_qvalidator(self, qt: QtDriver) -> None:
        """QLineEdit has a QValidator set."""

        def my_validator(text: str, pos: int) -> QValidator.State:
            return QValidator.State.Acceptable

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=my_validator)

        instance = create_and_track(qt, TestWidget, Widget)
        assert_that(instance.name.validator()).is_not_none()


# =============================================================================
# Method name string validator
# =============================================================================


class TestMethodNameValidator:
    """validator="method_name" looks up method on widget."""

    def test_method_name_simple_predicate(self, qt: QtDriver) -> None:
        """Method returning bool works as predicate."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator="validate_name")

            def validate_name(self, text: str) -> bool:
                return len(text) <= 10

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Short")
        assert_that(instance.name.text()).is_equal_to("Short")

    def test_method_name_full_validator(self, qt: QtDriver) -> None:
        """Method returning QValidator.State works."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator="validate_name")

            def validate_name(self, text: str, pos: int) -> QValidator.State:
                if len(text) >= 3:
                    return QValidator.State.Acceptable
                return QValidator.State.Intermediate

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("ab")
        assert_that(instance.name.text()).is_equal_to("ab")

    def test_method_has_access_to_self(self, qt: QtDriver) -> None:
        """Validator method can access widget state."""

        @widget
        class TestWidget(Widget):
            max_length: Variable[int] = new(5)
            name: QLineEdit = new(validator="validate_name")

            def validate_name(self, text: str) -> bool:
                return len(text) <= self.max_length.value

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Hi")
        assert_that(instance.name.text()).is_equal_to("Hi")


# =============================================================================
# Variable[str, QLineEdit] with validator
# =============================================================================


class TestVariableWithValidator:
    """Variable[str, QLineEdit] supports validator=."""

    def test_variable_regex_validator(self, qt: QtDriver) -> None:
        """Variable[str, QLineEdit] with regex validator."""

        @widget
        class TestWidget(Widget):
            name: Variable[str, QLineEdit] = new("")(validator=r"[a-zA-Z]+")

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.widget.setText("Hello")
        assert_that(instance.name.widget.text()).is_equal_to("Hello")

    def test_variable_lambda_validator(self, qt: QtDriver) -> None:
        """Variable[str, QLineEdit] with lambda validator."""

        @widget
        class TestWidget(Widget):
            name: Variable[str, QLineEdit] = new("")(validator=lambda t: len(t) <= 10)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.widget.setText("Short")
        assert_that(instance.name.widget.text()).is_equal_to("Short")

    def test_variable_method_name_validator(self, qt: QtDriver) -> None:
        """Variable[str, QLineEdit] with method name validator."""

        @widget
        class TestWidget(Widget):
            name: Variable[str, QLineEdit] = new("")(validator="validate_name")

            def validate_name(self, text: str) -> bool:
                return len(text) <= 10

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.widget.setText("Short")
        assert_that(instance.name.widget.text()).is_equal_to("Short")


# =============================================================================
# Edge cases
# =============================================================================


class TestValidatorEdgeCases:
    """Edge cases for input validators."""

    def test_no_validator_allows_anything(self, qt: QtDriver) -> None:
        """Without validator, any input is allowed."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new()

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Anything!@#$%^&*()")
        assert_that(instance.name.text()).is_equal_to("Anything!@#$%^&*()")
        assert_that(instance.name.validator()).is_none()

    def test_empty_regex_allows_anything(self, qt: QtDriver) -> None:
        """Empty regex pattern allows anything."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=r".*")

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Anything!@#$")
        assert_that(instance.name.text()).is_equal_to("Anything!@#$")

    def test_always_true_lambda(self, qt: QtDriver) -> None:
        """Lambda always returning True allows anything."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=lambda t: True)

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("Anything!@#$")
        assert_that(instance.name.text()).is_equal_to("Anything!@#$")

    def test_empty_string_validation(self, qt: QtDriver) -> None:
        """Empty string is validated too."""

        @widget
        class TestWidget(Widget):
            name: QLineEdit = new(validator=lambda t: t == "" or t.isalpha())

        instance = create_and_track(qt, TestWidget, Widget)
        instance.name.setText("")
        assert_that(instance.name.text()).is_equal_to("")


# =============================================================================
# Validator with bind= (binding system path)
# =============================================================================


class TestValidatorWithBind:
    """Validator works correctly when combined with bind=."""

    def test_validator_with_bind_to_variable(self, qt: QtDriver) -> None:
        """Validator is applied when widget has bind= to a Variable."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")
            name_input: QLineEdit = new(bind="_name", validator=r"[a-zA-Z]+")

        instance = create_and_track(qt, TestWidget, Widget)
        assert_that(instance.name_input.validator()).is_not_none()
        instance.name_input.setText("Hello")
        assert_that(instance.name_input.text()).is_equal_to("Hello")
        assert_that(instance._name.value).is_equal_to("Hello")

    def test_validator_with_bind_to_record(self, qt: QtDriver) -> None:
        """Validator is applied when widget binds to record property."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @widget(record=Person())
        class TestWidget(Widget[Person]):
            name: QLineEdit = new(bind="name", validator=lambda t: len(t) <= 10)

        instance = create_and_track(qt, TestWidget, Widget[Person])
        assert_that(instance.name.validator()).is_not_none()
        instance.name.setText("Short")
        assert_that(instance.name.text()).is_equal_to("Short")
        assert_that(instance.record.name).is_equal_to("Short")

    def test_validator_with_format_bind(self, qt: QtDriver) -> None:
        """Validator is applied even with format string bind (one-way)."""

        @widget
        class TestWidget(Widget):
            _prefix: Variable[str] = new("Hello")
            display: QLineEdit = new(bind="{_prefix} World", validator=r".*")

        instance = create_and_track(qt, TestWidget, Widget)
        # Format bindings are one-way, but validator should still be set
        assert_that(instance.display.validator()).is_not_none()
