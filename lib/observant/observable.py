"""Observable - A reactive value that notifies on change."""

from __future__ import annotations

from collections.abc import Callable

# Validator returns None (valid) or str/list[str] (errors)
type ValidatorResult = None | str | list[str]
type ValidatorFn[T] = Callable[[T], ValidatorResult]


class Observable[T]:
    """A value that notifies listeners when it changes."""

    def __init__(self, value: T, *, dirty_tracking: bool = True, validation: bool = True) -> None:
        self._value = value
        self._clean_value = value
        self._callbacks: list[Callable[[T], None]] = []
        # Nested Observable for dirty state (without its own tracking to avoid recursion)
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False, validation=False) if dirty_tracking else None

        # Validation - named validators, observable errors (disabled for internal observables)
        self._validators: dict[str, ValidatorFn[T]] = {}
        if validation:
            self._validation_errors: Observable[dict[str, list[str]]] | None = Observable({}, dirty_tracking=False, validation=False)
            self._validation_error_messages: Observable[list[str]] | None = Observable([], dirty_tracking=False, validation=False)
            self._is_valid: Observable[bool] | None = Observable(True, dirty_tracking=False, validation=False)
        else:
            self._validation_errors = None
            self._validation_error_messages = None
            self._is_valid = None

    def get(self) -> T:
        """Get the current value."""
        return self._value

    def set(self, value: T) -> None:
        """Set a new value and notify listeners."""
        self._value = value

        # Update dirty state if tracking
        if self._is_dirty is not None:
            now_dirty = self._value != self._clean_value
            if self._is_dirty.get() != now_dirty:
                self._is_dirty.set(now_dirty)

        # Re-validate
        self._validate()

        for callback in self._callbacks:
            callback(value)

    def on_change(self, callback: Callable[[T], None]) -> None:
        """Register a callback to be called when the value changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        if self._is_dirty is None:
            raise RuntimeError("Dirty tracking not enabled for this Observable")
        return self._is_dirty

    def reset_dirty(self) -> None:
        """Mark current value as clean."""
        self._clean_value = self._value
        if self._is_dirty is not None:
            self._is_dirty.set(False)

    def __bool__(self) -> bool:
        """Allow Observable to be used in boolean context."""
        return bool(self._value)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[T]) -> None:
        """Add a named validator. Validator returns None (valid) or str/list[str] (errors)."""
        self._validators[name] = validator
        self._validate()

    def remove_validator(self, name: str) -> None:
        """Remove a named validator."""
        if name in self._validators:
            del self._validators[name]
            self._validate()

    def _validate(self) -> None:
        """Run all validators and update state."""
        if self._is_valid is None:
            return  # Validation disabled

        if not self._validators:
            # No validators = always valid
            assert self._validation_errors is not None
            assert self._validation_error_messages is not None
            self._validation_errors.set({})
            self._validation_error_messages.set([])
            if not self._is_valid.get():
                self._is_valid.set(True)
            return

        errors_dict: dict[str, list[str]] = {}
        all_messages: list[str] = []

        for name, validator in self._validators.items():
            result = validator(self._value)
            if result is None:
                errors_dict[name] = []
            elif isinstance(result, str):
                errors_dict[name] = [result]
                all_messages.append(result)
            else:  # list[str]
                errors_dict[name] = list(result)
                all_messages.extend(result)

        # Update observables (we know they're not None because _is_valid is not None)
        assert self._validation_errors is not None
        assert self._validation_error_messages is not None
        self._validation_errors.set(errors_dict)
        self._validation_error_messages.set(all_messages)

        is_valid = len(all_messages) == 0
        if self._is_valid.get() != is_valid:
            self._is_valid.set(is_valid)

    @property
    def is_valid(self) -> Observable[bool]:
        """Validity state. Bindable."""
        if self._is_valid is None:
            raise RuntimeError("Validation not enabled for this Observable")
        return self._is_valid

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        if self._validation_errors is None:
            raise RuntimeError("Validation not enabled for this Observable")
        return self._validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        if self._validation_error_messages is None:
            raise RuntimeError("Validation not enabled for this Observable")
        return self._validation_error_messages
