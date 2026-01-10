"""ObservableProxy - A reactive wrapper for any object."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast, override

from .observable import Observable, ValidatorFn
from .observable_dict import ObservableDict
from .observable_list import ObservableList


def _is_primitive(value: Any) -> bool:
    """Check if value is a primitive type."""
    return isinstance(value, (str, int, float, bool, type(None)))


class ObservableProxy[T]:
    """A reactive wrapper that makes any object's fields observable.

    Fields are lazily wrapped as Observables on first access.
    Nested objects become nested ObservableProxies.
    """

    def __init__(self, target: T, *, dirty_tracking: bool = True, validation: bool = True) -> None:
        # Use object.__setattr__ to bypass our __setattr__
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_field_observables", {})
        object.__setattr__(self, "_field_lists", {})
        object.__setattr__(self, "_field_dicts", {})
        object.__setattr__(self, "_nested_proxies", {})
        object.__setattr__(self, "_callbacks", [])
        object.__setattr__(self, "_dirty_tracking", dirty_tracking)
        object.__setattr__(self, "_validation", validation)
        object.__setattr__(
            self,
            "_is_dirty",
            Observable[bool](False, dirty_tracking=False, validation=False) if dirty_tracking else None,
        )

        # Validation
        object.__setattr__(self, "_validators", {})
        if validation:
            object.__setattr__(self, "_validation_errors", Observable({}, dirty_tracking=False, validation=False))
            object.__setattr__(self, "_validation_error_messages", Observable([], dirty_tracking=False, validation=False))
            object.__setattr__(self, "_is_valid", Observable(True, dirty_tracking=False, validation=False))
        else:
            object.__setattr__(self, "_validation_errors", None)
            object.__setattr__(self, "_validation_error_messages", None)
            object.__setattr__(self, "_is_valid", None)

    def _get_or_create_field_observable(self, name: str) -> Observable[Any]:
        """Get or create an Observable for a field."""
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")

        if name not in field_observables:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")
            validation = object.__getattribute__(self, "_validation")

            obs = Observable[Any](value, dirty_tracking=dirty_tracking, validation=validation)

            # When this field changes, update the target and notify
            def on_field_change(new_value: Any, field_name: str = name) -> None:
                target = object.__getattribute__(self, "_target")
                setattr(target, field_name, new_value)
                self._update_dirty_state()
                self._validate()  # Re-run own validators
                self._update_valid_state()
                self._notify_change()

            obs.on_change(on_field_change)

            # Also subscribe to field's validity changes
            if validation:
                obs.is_valid.on_change(lambda _: self._update_valid_state())

            field_observables[name] = obs

        return field_observables[name]

    def _get_or_create_field_list(self, name: str) -> ObservableList[Any]:
        """Get or create an ObservableList for a list field."""
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")

        if name not in field_lists:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")
            validation = object.__getattribute__(self, "_validation")

            obs_list = ObservableList[Any](value, dirty_tracking=dirty_tracking, validation=validation)

            # When list changes, update the target and notify
            def on_list_change(field_name: str = name) -> None:
                target = object.__getattribute__(self, "_target")
                setattr(target, field_name, obs_list.to_list())
                self._update_dirty_state()
                self._validate()  # Re-run own validators
                self._update_valid_state()
                self._notify_change()

            obs_list.on_change(on_list_change)

            # Subscribe to list's validity changes
            if validation:
                obs_list.is_valid.on_change(lambda _: self._update_valid_state())

            field_lists[name] = obs_list

        return field_lists[name]

    def _get_or_create_field_dict(self, name: str) -> ObservableDict[Any, Any]:
        """Get or create an ObservableDict for a dict field."""
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")

        if name not in field_dicts:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")
            validation = object.__getattribute__(self, "_validation")

            obs_dict = ObservableDict[Any, Any](value, dirty_tracking=dirty_tracking, validation=validation)

            # When dict changes, update the target and notify
            def on_dict_change(field_name: str = name) -> None:
                target = object.__getattribute__(self, "_target")
                setattr(target, field_name, obs_dict.to_dict())
                self._update_dirty_state()
                self._validate()  # Re-run own validators
                self._update_valid_state()
                self._notify_change()

            obs_dict.on_change(on_dict_change)

            # Subscribe to dict's validity changes
            if validation:
                obs_dict.is_valid.on_change(lambda _: self._update_valid_state())

            field_dicts[name] = obs_dict

        return field_dicts[name]

    def _get_or_create_nested_proxy(self, name: str) -> ObservableProxy[Any]:
        """Get or create a nested ObservableProxy for a complex field."""
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        if name not in nested_proxies:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")
            validation = object.__getattribute__(self, "_validation")

            proxy = ObservableProxy[Any](value, dirty_tracking=dirty_tracking, validation=validation)

            # When nested proxy changes, propagate up
            def on_nested_change() -> None:
                self._update_dirty_state()  # Update dirty state first
                self._validate()  # Re-run own validators
                self._update_valid_state()  # Update valid state
                self._notify_change()  # Then notify

            proxy.on_change(on_nested_change)

            # Subscribe to nested proxy's validity changes
            if validation:
                proxy.is_valid.on_change(lambda _: self._update_valid_state())

            nested_proxies[name] = proxy

        return nested_proxies[name]

    def _notify_change(self) -> None:
        """Notify all change listeners."""
        callbacks: list[Callable[[], None]] = object.__getattribute__(self, "_callbacks")
        for callback in callbacks:
            callback()

    def _update_dirty_state(self) -> None:
        """Update aggregated dirty state from all fields."""
        is_dirty_obs: Observable[bool] | None = object.__getattribute__(self, "_is_dirty")
        if is_dirty_obs is None:
            return

        dirty_tracking: bool = object.__getattribute__(self, "_dirty_tracking")
        if not dirty_tracking:
            return

        # Check if any field wrapper is dirty
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        any_dirty = False

        for obs in field_observables.values():
            if obs.is_dirty.get():
                any_dirty = True
                break

        if not any_dirty:
            for obs_list in field_lists.values():
                if obs_list.is_dirty.get():
                    any_dirty = True
                    break

        if not any_dirty:
            for obs_dict in field_dicts.values():
                if obs_dict.is_dirty.get():
                    any_dirty = True
                    break

        if not any_dirty:
            for proxy in nested_proxies.values():
                if proxy.is_dirty.get():
                    any_dirty = True
                    break

        if is_dirty_obs.get() != any_dirty:
            is_dirty_obs.set(any_dirty)

    def _update_valid_state(self) -> None:
        """Update aggregated valid state from all fields."""
        is_valid_obs: Observable[bool] | None = object.__getattribute__(self, "_is_valid")
        if is_valid_obs is None:
            return

        validation: bool = object.__getattribute__(self, "_validation")
        if not validation:
            return

        # Check if all field wrappers are valid
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        all_valid = True

        for obs in field_observables.values():
            if not obs.is_valid.get():
                all_valid = False
                break

        if all_valid:
            for obs_list in field_lists.values():
                if not obs_list.is_valid.get():
                    all_valid = False
                    break

        if all_valid:
            for obs_dict in field_dicts.values():
                if not obs_dict.is_valid.get():
                    all_valid = False
                    break

        if all_valid:
            for proxy in nested_proxies.values():
                if not proxy.is_valid.get():
                    all_valid = False
                    break

        # Also check own validators
        if all_valid:
            validation_error_messages: Observable[list[str]] | None = object.__getattribute__(self, "_validation_error_messages")
            if validation_error_messages is not None and validation_error_messages.get():
                all_valid = False

        if is_valid_obs.get() != all_valid:
            is_valid_obs.set(all_valid)

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback for any field change."""
        callbacks: list[Callable[[], None]] = object.__getattribute__(self, "_callbacks")
        if callback not in callbacks:
            callbacks.append(callback)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Aggregated dirty state across all fields."""
        is_dirty_obs: Observable[bool] | None = object.__getattribute__(self, "_is_dirty")
        if is_dirty_obs is None:
            raise RuntimeError("Dirty tracking not enabled for this ObservableProxy")
        return is_dirty_obs

    def reset_dirty(self) -> None:
        """Reset dirty state for all fields."""
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        for obs in field_observables.values():
            obs.reset_dirty()

        for obs_list in field_lists.values():
            obs_list.reset_dirty()

        for obs_dict in field_dicts.values():
            obs_dict.reset_dirty()

        for proxy in nested_proxies.values():
            proxy.reset_dirty()

        is_dirty_obs: Observable[bool] | None = object.__getattribute__(self, "_is_dirty")
        if is_dirty_obs is not None:
            is_dirty_obs.set(False)

    @property
    def dirty_fields(self) -> list[str]:
        """Get list of dirty field names."""
        dirty: list[str] = []

        dirty_tracking: bool = object.__getattribute__(self, "_dirty_tracking")
        if not dirty_tracking:
            return dirty

        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        for name, obs in field_observables.items():
            if obs.is_dirty.get():
                dirty.append(name)

        for name, obs_list in field_lists.items():
            if obs_list.is_dirty.get():
                dirty.append(name)

        for name, obs_dict in field_dicts.items():
            if obs_dict.is_dirty.get():
                dirty.append(name)

        for name, proxy in nested_proxies.items():
            if proxy.is_dirty.get():
                dirty.append(name)

        return dirty

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[T]) -> None:
        """Add a named validator. Validator returns None (valid) or str/list[str] (errors)."""
        validators: dict[str, ValidatorFn[T]] = object.__getattribute__(self, "_validators")
        validators[name] = validator
        self._validate()

    def _validate(self) -> None:
        """Run own validators and update state."""
        is_valid_obs: Observable[bool] | None = object.__getattribute__(self, "_is_valid")
        if is_valid_obs is None:
            return

        validators: dict[str, ValidatorFn[T]] = object.__getattribute__(self, "_validators")
        if not validators:
            return

        target: T = object.__getattribute__(self, "_target")
        errors_dict: dict[str, list[str]] = {}
        all_messages: list[str] = []

        for name, validator in validators.items():
            result = validator(target)
            if result is None:
                errors_dict[name] = []
            elif isinstance(result, str):
                errors_dict[name] = [result]
                all_messages.append(result)
            else:  # list[str]
                errors_dict[name] = list(result)
                all_messages.extend(result)

        validation_errors: Observable[dict[str, list[str]]] | None = object.__getattribute__(self, "_validation_errors")
        validation_error_messages: Observable[list[str]] | None = object.__getattribute__(self, "_validation_error_messages")

        if validation_errors is not None:
            validation_errors.set(errors_dict)
        if validation_error_messages is not None:
            validation_error_messages.set(all_messages)

        self._update_valid_state()

    @property
    def is_valid(self) -> Observable[bool]:
        """Aggregated validity state across all fields."""
        is_valid_obs: Observable[bool] | None = object.__getattribute__(self, "_is_valid")
        if is_valid_obs is None:
            raise RuntimeError("Validation not enabled for this ObservableProxy")
        return is_valid_obs

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        validation_errors: Observable[dict[str, list[str]]] | None = object.__getattribute__(self, "_validation_errors")
        if validation_errors is None:
            raise RuntimeError("Validation not enabled for this ObservableProxy")
        return validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        validation_error_messages: Observable[list[str]] | None = object.__getattribute__(self, "_validation_error_messages")
        if validation_error_messages is None:
            raise RuntimeError("Validation not enabled for this ObservableProxy")
        return validation_error_messages

    @property
    def invalid_fields(self) -> list[str]:
        """Get list of invalid field names."""
        invalid: list[str] = []

        validation: bool = object.__getattribute__(self, "_validation")
        if not validation:
            return invalid

        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        for name, obs in field_observables.items():
            if not obs.is_valid.get():
                invalid.append(name)

        for name, obs_list in field_lists.items():
            if not obs_list.is_valid.get():
                invalid.append(name)

        for name, obs_dict in field_dicts.items():
            if not obs_dict.is_valid.get():
                invalid.append(name)

        for name, proxy in nested_proxies.items():
            if not proxy.is_valid.get():
                invalid.append(name)

        return invalid

    def unwrap(self) -> T:
        """Get the underlying target object."""
        return object.__getattribute__(self, "_target")

    def replace_target(self, new_target: T) -> None:
        """Replace the underlying target object and update all field observables.

        This triggers change notifications so all bound widgets update.

        Args:
            new_target: The new object to wrap.
        """
        # Replace the target
        object.__setattr__(self, "_target", new_target)

        # Update all existing field observables with new values
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        for name, obs in field_observables.items():
            if hasattr(new_target, name):
                new_value = getattr(new_target, name)
                obs.set(new_value)

        # Update all existing field lists
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")
        for name, obs_list in field_lists.items():
            if hasattr(new_target, name):
                new_list_value = getattr(new_target, name)
                obs_list.clear()
                if isinstance(new_list_value, list):
                    obs_list.extend(cast(list[Any], new_list_value))

        # Update all existing field dicts
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")
        for name, obs_dict in field_dicts.items():
            if hasattr(new_target, name):
                new_dict_value = getattr(new_target, name)
                obs_dict.clear()
                if isinstance(new_dict_value, dict):
                    obs_dict.update(cast(dict[Any, Any], new_dict_value))

        # Update all nested proxies recursively
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")
        for name, proxy in nested_proxies.items():
            if hasattr(new_target, name):
                new_value = getattr(new_target, name)
                proxy.replace_target(new_value)

        # Update dirty/valid state and notify
        self._update_dirty_state()
        self._validate()
        self._update_valid_state()
        self._notify_change()

    def _parse_path_segments(self, path: str) -> list[tuple[str, bool]]:
        """Parse a path into segments with optional flags.

        'a.b?.c' -> [('a', False), ('b', True), ('c', False)]

        The boolean indicates if the PREVIOUS segment used optional chaining.
        So 'b?.c' means if b is None, don't error.
        """
        segments: list[tuple[str, bool]] = []
        # Replace ?. with a marker, then split on .
        parts = path.replace("?.", "\x00.").split(".")
        for part in parts:
            is_optional = part.endswith("\x00")
            name = part.rstrip("\x00")
            if name:  # Skip empty parts
                segments.append((name, is_optional))
        return segments

    def observable_for_path(self, path: str) -> Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any]:
        """Get observable for a dotted path like 'dog.breed.name'.

        Handles optional chaining: 'dog.breed?.name' returns None-safe observable.
        If breed is None, returns an Observable holding None instead of erroring.

        Args:
            path: Dotted path like 'name', 'dog.breed', or 'dog.breed?.name'

        Returns:
            The Observable/ObservableList/ObservableDict/ObservableProxy at the path.
        """
        segments = self._parse_path_segments(path)

        current: Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any] = self
        for name, is_optional in segments:
            # If we have an ObservableProxy, traverse into it
            if isinstance(current, ObservableProxy):
                target = object.__getattribute__(current, "_target")

                # Check if target is None (from optional chaining)
                if target is None:
                    return Observable[Any](None)

                # Check if field exists
                if not hasattr(target, name):
                    if is_optional:
                        return Observable[Any](None)
                    raise AttributeError(f"'{type(target).__name__}' object has no attribute '{name}'")

                # Get the value to check if it's None before optional chaining
                value = getattr(target, name)
                if value is None and is_optional:
                    return Observable[Any](None)

                # Get the observable/proxy for this field
                current = getattr(current, name)
            else:
                # Can't traverse into Observable/ObservableList/ObservableDict
                raise ValueError(f"Cannot traverse path '{name}' into {type(current).__name__}")

        return current

    def __getattr__(self, name: str) -> Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any]:
        """Get a field as an Observable, ObservableList, ObservableDict, or nested proxy."""
        # Check if this is an internal attribute
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        target = object.__getattribute__(self, "_target")

        # Make sure field exists on target
        if not hasattr(target, name):
            raise AttributeError(f"'{type(target).__name__}' object has no attribute '{name}'")

        value = getattr(target, name)

        # For primitives, return Observable
        if _is_primitive(value):
            return self._get_or_create_field_observable(name)

        # For lists, return ObservableList
        if isinstance(value, list):
            return self._get_or_create_field_list(name)

        # For dicts, return ObservableDict
        if isinstance(value, dict):
            return self._get_or_create_field_dict(name)

        # For complex types, return nested proxy
        return self._get_or_create_nested_proxy(name)

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """Set a field value."""
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        target = object.__getattribute__(self, "_target")

        # For primitives, always go through an Observable to track dirty state properly
        if _is_primitive(value):
            # This creates the Observable if it doesn't exist, ensuring dirty_fields works
            obs = self._get_or_create_field_observable(name)
            obs.set(value)
        else:
            # For complex types (lists, dicts, objects), set directly and notify
            setattr(target, name, value)
            # Mark as dirty since we modified a field directly
            dirty_tracking: bool = object.__getattribute__(self, "_dirty_tracking")
            if dirty_tracking:
                is_dirty_obs: Observable[bool] | None = object.__getattribute__(self, "_is_dirty")
                if is_dirty_obs is not None and not is_dirty_obs.get():
                    is_dirty_obs.set(True)
            self._notify_change()

    @override
    def __repr__(self) -> str:
        target = object.__getattribute__(self, "_target")
        return f"ObservableProxy({target!r})"
