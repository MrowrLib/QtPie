# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false
# pyright: reportOperatorIssue=false
"""Tests for Observable validation support."""

from dataclasses import dataclass

from assertpy import assert_that
from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet


class TestObservableValidation:
    """Test Observable[T] validation."""

    def test_add_named_validator(self) -> None:
        """Can add a named validator."""
        obs = Observable("hello")
        obs.add_validator("required", lambda v: None if v else "Required")

        assert_that(obs.is_valid.get()).is_true()

    def test_is_valid_starts_true(self) -> None:
        """Observable starts valid before any validators."""
        obs = Observable("")
        assert_that(obs.is_valid.get()).is_true()

    def test_invalid_after_bad_value(self) -> None:
        """Observable becomes invalid when value fails validation."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")

        assert_that(obs.is_valid.get()).is_false()

    def test_validation_errors_dict_by_name(self) -> None:
        """validation_errors returns dict keyed by validator name."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")
        obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

        errors = obs.validation_errors.get()
        assert_that(errors).contains_key("required", "min_len")
        assert_that(errors["required"]).is_equal_to(["Required"])
        assert_that(errors["min_len"]).is_equal_to(["Too short"])

    def test_validation_error_messages_flat(self) -> None:
        """validation_error_messages returns flat list."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")
        obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

        msgs = obs.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Too short")

    def test_validator_returns_list(self) -> None:
        """Validator can return list of errors."""
        obs = Observable("")
        obs.add_validator("multi", lambda v: ["Error 1", "Error 2"] if not v else None)

        errors = obs.validation_errors.get()
        assert_that(errors["multi"]).is_equal_to(["Error 1", "Error 2"])

    def test_revalidates_on_set(self) -> None:
        """Validation runs again on set()."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")

        assert_that(obs.is_valid.get()).is_false()

        obs.set("hello")
        assert_that(obs.is_valid.get()).is_true()

    def test_multiple_validators_same_observable(self) -> None:
        """Multiple validators all run."""
        obs = Observable("ab")
        obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")
        obs.add_validator("starts_a", lambda v: None if v.startswith("a") else "Must start with a")

        # fails min_len only
        assert_that(obs.is_valid.get()).is_false()
        assert_that(obs.validation_errors.get()["min_len"]).is_equal_to(["Too short"])
        assert_that(obs.validation_errors.get()["starts_a"]).is_equal_to([])

        obs.set("abc")
        assert_that(obs.is_valid.get()).is_true()

    def test_is_valid_is_observable(self) -> None:
        """is_valid is itself an Observable."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")

        transitions: list[bool] = []
        obs.is_valid.on_change(lambda v: transitions.append(v))

        obs.set("hello")  # now valid
        assert_that(transitions).contains(True)

    def test_remove_validator(self) -> None:
        """Can remove a validator by name."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")

        assert_that(obs.is_valid.get()).is_false()

        obs.remove_validator("required")
        assert_that(obs.is_valid.get()).is_true()
        assert_that(obs.validation_errors.get()).is_empty()

    def test_remove_validator_nonexistent(self) -> None:
        """Removing nonexistent validator is a no-op."""
        obs = Observable("hello")
        obs.add_validator("required", lambda v: None if v else "Required")

        # Should not raise
        obs.remove_validator("nonexistent")
        assert_that(obs.is_valid.get()).is_true()

    def test_remove_one_of_multiple_validators(self) -> None:
        """Can remove one validator while keeping others."""
        obs = Observable("")
        obs.add_validator("required", lambda v: None if v else "Required")
        obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

        assert_that(obs.validation_errors.get()).contains_key("required", "min_len")

        obs.remove_validator("required")
        assert_that(obs.validation_errors.get()).does_not_contain_key("required")
        assert_that(obs.validation_errors.get()).contains_key("min_len")
        assert_that(obs.is_valid.get()).is_false()  # Still invalid due to min_len


class TestObservableListValidation:
    """Test ObservableList[T] validation."""

    def test_list_validation(self) -> None:
        """ObservableList can have validators."""
        lst = ObservableList[str]([])
        lst.add_validator("not_empty", lambda items: None if items else "List cannot be empty")

        assert_that(lst.is_valid.get()).is_false()
        assert_that(lst.validation_error_messages.get()).is_equal_to(["List cannot be empty"])

        lst.append("item")
        assert_that(lst.is_valid.get()).is_true()

    def test_list_validation_on_mutation(self) -> None:
        """Validation runs on list mutations."""
        lst = ObservableList[int]([1, 2, 3])
        lst.add_validator("max_3", lambda items: None if len(items) <= 3 else "Max 3 items")

        assert_that(lst.is_valid.get()).is_true()

        lst.append(4)
        assert_that(lst.is_valid.get()).is_false()

        lst.pop()
        assert_that(lst.is_valid.get()).is_true()

    def test_list_remove_validator(self) -> None:
        """Can remove a validator from ObservableList."""
        lst = ObservableList[str]([])
        lst.add_validator("not_empty", lambda items: None if items else "List cannot be empty")

        assert_that(lst.is_valid.get()).is_false()

        lst.remove_validator("not_empty")
        assert_that(lst.is_valid.get()).is_true()
        assert_that(lst.validation_errors.get()).is_empty()


class TestObservableDictValidation:
    """Test ObservableDict[K, V] validation."""

    def test_dict_validation(self) -> None:
        """ObservableDict can have validators."""
        dct = ObservableDict[str, int]({"a": 1})
        dct.add_validator(
            "has_required",
            lambda d: None if "required" in d else "Missing 'required' key",
        )

        assert_that(dct.is_valid.get()).is_false()
        assert_that(dct.validation_error_messages.get()).is_equal_to(["Missing 'required' key"])

        dct["required"] = 42
        assert_that(dct.is_valid.get()).is_true()

    def test_dict_remove_validator(self) -> None:
        """Can remove a validator from ObservableDict."""
        dct = ObservableDict[str, int]({"a": 1})
        dct.add_validator(
            "has_required",
            lambda d: None if "required" in d else "Missing 'required' key",
        )

        assert_that(dct.is_valid.get()).is_false()

        dct.remove_validator("has_required")
        assert_that(dct.is_valid.get()).is_true()
        assert_that(dct.validation_errors.get()).is_empty()


class TestObservableSetValidation:
    """Test ObservableSet[T] validation."""

    def test_set_validation(self) -> None:
        """ObservableSet can have validators."""
        s = ObservableSet[str](set())
        s.add_validator("not_empty", lambda items: None if items else "Set cannot be empty")

        assert_that(s.is_valid.get()).is_false()
        assert_that(s.validation_error_messages.get()).is_equal_to(["Set cannot be empty"])

        s.add("item")
        assert_that(s.is_valid.get()).is_true()

    def test_set_remove_validator(self) -> None:
        """Can remove a validator from ObservableSet."""
        s = ObservableSet[str](set())
        s.add_validator("not_empty", lambda items: None if items else "Set cannot be empty")

        assert_that(s.is_valid.get()).is_false()

        s.remove_validator("not_empty")
        assert_that(s.is_valid.get()).is_true()
        assert_that(s.validation_errors.get()).is_empty()


class TestObservableProxyValidation:
    """Test ObservableProxy[T] validation."""

    def test_proxy_aggregates_field_validity(self) -> None:
        """Proxy is_valid aggregates from child fields."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        proxy: ObservableProxy[Person] = ObservableProxy(Person())

        # Add validator to a field
        proxy.name.add_validator("required", lambda v: None if v else "Name required")

        assert_that(proxy.is_valid.get()).is_false()

        proxy.name.set("Alice")
        assert_that(proxy.is_valid.get()).is_true()

    def test_proxy_own_validators(self) -> None:
        """Proxy can have its own validators on the whole object."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        proxy: ObservableProxy[Person] = ObservableProxy(Person())
        proxy.add_validator(
            "adult_named",
            lambda p: None if p.name and p.age >= 18 else "Must be named adult",
        )

        assert_that(proxy.is_valid.get()).is_false()

        proxy.name.set("Bob")
        proxy.age.set(21)
        # Still need to trigger re-validation for own validators
        # The proxy re-validates on field changes via _notify_change

    def test_invalid_fields_list(self) -> None:
        """Proxy can list which fields are invalid."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        proxy: ObservableProxy[Person] = ObservableProxy(Person())
        proxy.name.add_validator("required", lambda v: None if v else "Required")
        proxy.age.add_validator("positive", lambda v: None if v > 0 else "Must be positive")

        invalid = proxy.invalid_fields
        assert_that(invalid).contains("name", "age")

        proxy.name.set("Alice")
        invalid = proxy.invalid_fields
        assert_that(invalid).contains("age")
        assert_that(invalid).does_not_contain("name")

    def test_proxy_remove_own_validator(self) -> None:
        """Can remove proxy's own validator."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        proxy: ObservableProxy[Person] = ObservableProxy(Person())
        proxy.add_validator(
            "adult_named",
            lambda p: None if p.name and p.age >= 18 else "Must be named adult",
        )

        assert_that(proxy.is_valid.get()).is_false()

        proxy.remove_validator("adult_named")
        assert_that(proxy.is_valid.get()).is_true()
        assert_that(proxy.validation_errors.get()).is_empty()

    def test_proxy_remove_field_validator(self) -> None:
        """Can remove validator from proxy field."""

        @dataclass
        class Person:
            name: str = ""

        proxy: ObservableProxy[Person] = ObservableProxy(Person())
        proxy.name.add_validator("required", lambda v: None if v else "Required")

        assert_that(proxy.is_valid.get()).is_false()

        proxy.name.remove_validator("required")
        assert_that(proxy.name.is_valid.get()).is_true()
        assert_that(proxy.is_valid.get()).is_true()
