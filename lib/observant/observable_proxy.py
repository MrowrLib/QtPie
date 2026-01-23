"""ObservableProxy - A reactive wrapper for any object."""

from __future__ import annotations

import logging
import weakref
from collections.abc import Callable
from typing import Any, cast, override

from .observable import Observable, ValidatorFn
from .observable_dict import ObservableDict
from .observable_list import ObservableList

logger = logging.getLogger("qtpie.observant.proxy")

# Global registry mapping raw object id -> list of weak refs to proxies wrapping them.
# This allows finding proxies for a given raw object (e.g., to subscribe to changes).
_proxy_registry: dict[int, list[weakref.ref[ObservableProxy[Any]]]] = {}

# Callbacks to be notified when a new proxy is registered for any object.
# Callback receives (target_object, proxy).
_on_proxy_registered_callbacks: list[Callable[[Any, ObservableProxy[Any]], None]] = []


def on_proxy_registered(callback: Callable[[Any, ObservableProxy[Any]], None]) -> None:
    """Register a callback to be notified when any new proxy is created.

    Args:
        callback: Function that receives (target_object, proxy) when a proxy is registered.
    """
    if callback not in _on_proxy_registered_callbacks:
        _on_proxy_registered_callbacks.append(callback)


def get_proxies_for(obj: Any) -> list[ObservableProxy[Any]]:
    """Get all active proxies that wrap a given object.

    Args:
        obj: The raw object to look up.

    Returns:
        List of ObservableProxy instances wrapping this object.
        Returns empty list if no proxies found.
    """
    obj_id = id(obj)
    if obj_id not in _proxy_registry:
        return []

    # Filter out dead refs and return live proxies
    live_proxies: list[ObservableProxy[Any]] = []
    dead_refs: list[weakref.ref[ObservableProxy[Any]]] = []

    for ref in _proxy_registry[obj_id]:
        proxy = ref()
        if proxy is not None:
            live_proxies.append(proxy)
        else:
            dead_refs.append(ref)

    # Clean up dead refs
    for ref in dead_refs:
        _proxy_registry[obj_id].remove(ref)

    # Remove entry if no proxies left
    if not _proxy_registry[obj_id]:
        del _proxy_registry[obj_id]

    return live_proxies


def _register_proxy(proxy: ObservableProxy[Any], target: Any) -> None:
    """Register a proxy in the global registry."""
    obj_id = id(target)
    if obj_id not in _proxy_registry:
        _proxy_registry[obj_id] = []

    # Add weak ref to proxy
    ref = weakref.ref(proxy)
    _proxy_registry[obj_id].append(ref)
    logger.warning(
        "DEBUG _register_proxy: target=%s (id=%d, total proxies=%d)",
        type(target).__name__,
        obj_id,
        len(_proxy_registry[obj_id]),
    )

    # Notify all registered callbacks
    for callback in _on_proxy_registered_callbacks:
        try:
            callback(target, proxy)
        except Exception:
            logger.exception("Error in on_proxy_registered callback")


def _unregister_proxy(proxy: ObservableProxy[Any], old_target: Any) -> None:
    """Unregister a proxy from the global registry for a specific target."""
    obj_id = id(old_target)
    if obj_id not in _proxy_registry:
        return

    # Find and remove the weak ref for this proxy
    refs_to_remove: list[weakref.ref[ObservableProxy[Any]]] = []
    for ref in _proxy_registry[obj_id]:
        p = ref()
        if p is None or p is proxy:
            refs_to_remove.append(ref)

    for ref in refs_to_remove:
        _proxy_registry[obj_id].remove(ref)

    # Remove entry if no proxies left
    if not _proxy_registry[obj_id]:
        del _proxy_registry[obj_id]


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
        # Observable for tracking when the target reference itself changes (via replace_target)
        # This is bidirectional: setting this observable also calls replace_target
        ref_obs = Observable[T](target, dirty_tracking=False, validation=False)
        object.__setattr__(self, "_reference_observable", ref_obs)
        object.__setattr__(self, "_ref_obs_updating", False)

        # Wire up bidirectional sync: when ref_obs is set externally, call replace_target
        def on_ref_obs_set(new_value: T) -> None:
            # Avoid infinite loop (replace_target also sets ref_obs)
            if object.__getattribute__(self, "_ref_obs_updating"):
                return
            object.__setattr__(self, "_ref_obs_updating", True)
            try:
                self.replace_target(new_value)
            finally:
                object.__setattr__(self, "_ref_obs_updating", False)

        ref_obs.on_change(on_ref_obs_set)

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

        # Register in global registry so others can find proxies for this target
        _register_proxy(self, target)

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
                # Also update any cached nested proxy for this field (handles Enum fields)
                nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")
                if field_name in nested_proxies:
                    # Replace the nested proxy's target with the new value
                    object.__setattr__(nested_proxies[field_name], "_target", new_value)
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
            def on_nested_change(field_name: str = name) -> None:
                logger.warning("DEBUG on_nested_change: field=%s, notifying parent proxy", field_name)
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

    def _notify_change(self, *, _from_sibling: bool = False) -> None:
        """Notify all change listeners.

        Args:
            _from_sibling: If True, this notification came from a sibling proxy.
                           We skip notifying other siblings to prevent infinite loops.
        """
        callbacks: list[Callable[[], None]] = object.__getattribute__(self, "_callbacks")
        if callbacks:
            target = object.__getattribute__(self, "_target")
            logger.warning(
                "ObservableProxy._notify_change: proxy=%d, target=%s (id=%d), callbacks=%d",
                id(self),
                type(target).__name__ if target else "None",
                id(target) if target else 0,
                len(callbacks),
            )
        for callback in callbacks:
            callback()

        # Notify sibling proxies (other proxies wrapping the same object)
        # Only do this for the originating change, not for sibling notifications
        if not _from_sibling:
            self._notify_sibling_proxies()

    def _notify_sibling_proxies(self) -> None:
        """Notify other proxies wrapping the same target object.

        When one proxy updates a field, all other proxies wrapping the same
        object need to know so their bindings update too.
        """
        target = object.__getattribute__(self, "_target")
        logger.warning(
            "DEBUG _notify_sibling_proxies: target=%s (id=%d)",
            type(target).__name__ if target else "None",
            id(target) if target else 0,
        )
        siblings = get_proxies_for(target)
        logger.warning(
            "DEBUG _notify_sibling_proxies: found %d siblings (including self)",
            len(siblings),
        )
        for sibling in siblings:
            if sibling is not self:
                logger.warning("DEBUG _notify_sibling_proxies: notifying sibling proxy")
                # Sync the sibling's field observables with the updated target values
                sibling._sync_from_target()
                # Notify the sibling's listeners (with flag to prevent infinite loop)
                sibling._notify_change(_from_sibling=True)

    def _sync_from_target(self) -> None:
        """Sync all field observables and nested proxies from the current target values.

        Called when a sibling proxy modifies the shared target object.
        """
        target = object.__getattribute__(self, "_target")
        logger.warning(
            "DEBUG _sync_from_target: proxy=%d, target=%s (id=%d)",
            id(self),
            type(target).__name__ if target else "None",
            id(target) if target else 0,
        )

        # Sync field observables
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")
        logger.warning("DEBUG _sync_from_target: field_observables=%s", list(field_observables.keys()))
        for name, obs in field_observables.items():
            if hasattr(target, name):
                current_target_value = getattr(target, name)
                # Only update if different to avoid unnecessary notifications
                if obs.get() != current_target_value:
                    # Use internal set to avoid triggering another round of sibling notifications
                    # pyright: ignore - internal cross-class access within observant package
                    obs._value = current_target_value  # pyright: ignore[reportPrivateUsage]
                    # Notify this observable's listeners
                    obs._notify_observers()  # pyright: ignore[reportPrivateUsage]

        # Sync nested proxies (e.g., for Enum fields accessed via getattr)
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")
        logger.warning("DEBUG _sync_from_target: nested_proxies=%s", list(nested_proxies.keys()))
        for name, proxy in nested_proxies.items():
            if hasattr(target, name):
                current_target_value = getattr(target, name)
                # If target value is a Variable-like object, get its actual value.
                # The nested proxy wraps the Variable's VALUE, not the Variable itself.
                if hasattr(current_target_value, "value") and hasattr(current_target_value, "observable"):
                    current_target_value = current_target_value.value
                current_proxy_target = object.__getattribute__(proxy, "_target")
                logger.warning(
                    "DEBUG _sync_from_target: nested '%s' current=%s (id=%d), target=%s (id=%d), same=%s",
                    name,
                    current_proxy_target,
                    id(current_proxy_target),
                    current_target_value,
                    id(current_target_value),
                    current_proxy_target is current_target_value,
                )
                # Only update if different
                if current_proxy_target is not current_target_value:
                    logger.warning("DEBUG _sync_from_target: updating nested proxy '%s' target", name)
                    object.__setattr__(proxy, "_target", current_target_value)
                    # Notify this nested proxy's listeners so widgets bound to it get updated.
                    # This is safe because _sync_from_target is called from sibling notification,
                    # and we're propagating the change DOWN to nested proxies.
                    proxy._notify_change()

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
            target = object.__getattribute__(self, "_target")
            logger.warning(
                "DEBUG on_change: proxy=%d, target=%s (id=%d), total_callbacks=%d",
                id(self),
                type(target).__name__ if target else "None",
                id(target) if target else 0,
                len(callbacks),
            )

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

    def remove_validator(self, name: str) -> None:
        """Remove a named validator."""
        validators: dict[str, ValidatorFn[T]] = object.__getattribute__(self, "_validators")
        if name in validators:
            del validators[name]
            self._validate()

    def _validate(self) -> None:
        """Run own validators and update state."""
        is_valid_obs: Observable[bool] | None = object.__getattribute__(self, "_is_valid")
        if is_valid_obs is None:
            return

        validators: dict[str, ValidatorFn[T]] = object.__getattribute__(self, "_validators")
        if not validators:
            # No validators = always valid
            validation_errors: Observable[dict[str, list[str]]] | None = object.__getattribute__(self, "_validation_errors")
            validation_error_messages: Observable[list[str]] | None = object.__getattribute__(self, "_validation_error_messages")
            if validation_errors is not None:
                validation_errors.set({})
            if validation_error_messages is not None:
                validation_error_messages.set([])
            if not is_valid_obs.get():
                is_valid_obs.set(True)
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

    @property
    def reference_observable(self) -> Observable[T]:
        """Get an Observable that tracks when the target reference changes.

        This is useful for observing when the entire object is replaced via replace_target(),
        as opposed to on_change() which fires for any field change.
        """
        return object.__getattribute__(self, "_reference_observable")

    def replace_target(self, new_target: T) -> None:
        """Replace the underlying target object and update all field observables.

        This triggers change notifications so all bound widgets update.

        Args:
            new_target: The new object to wrap.
        """
        # Get old target for registry update
        old_target = object.__getattribute__(self, "_target")

        logger.warning(
            "DEBUG replace_target: proxy=%d, old_target=%s (id=%d), new_target=%s (id=%d)",
            id(self),
            type(old_target).__name__ if old_target else "None",
            id(old_target) if old_target else 0,
            type(new_target).__name__ if new_target else "None",
            id(new_target) if new_target else 0,
        )

        # Replace the target
        object.__setattr__(self, "_target", new_target)

        # Re-register in global registry if target identity changed
        if id(old_target) != id(new_target):
            _unregister_proxy(self, old_target)
            _register_proxy(self, new_target)

        # Update reference observable (for observers tracking when the whole object changes)
        # Set flag to avoid infinite loop from bidirectional sync
        object.__setattr__(self, "_ref_obs_updating", True)
        try:
            ref_obs: Observable[T] = object.__getattribute__(self, "_reference_observable")
            ref_obs.set(new_target)
        finally:
            object.__setattr__(self, "_ref_obs_updating", False)

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
            # Check for Variable-like objects (have .observable that is an ObservableProxy)
            # This handles qtpie.Variable without coupling observant to qtpie
            if not isinstance(current, ObservableProxy) and hasattr(current, "observable"):
                inner = getattr(current, "observable", None)
                if isinstance(inner, ObservableProxy):
                    current = inner  # pyright: ignore[reportUnknownVariableType]

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

        # If already an Observable type, return it directly (don't re-wrap)
        if isinstance(value, (Observable, ObservableList, ObservableDict, ObservableProxy)):
            return value  # pyright: ignore[reportUnknownVariableType]

        # Check for Variable-like objects (have .observable property that returns an Observable)
        # This handles qtpie.Variable without coupling observant to qtpie
        # NOTE: Must check BEFORE callable check since Variable is callable (__call__)
        if hasattr(value, "observable"):
            inner_obs = getattr(value, "observable", None)
            if isinstance(inner_obs, (Observable, ObservableList, ObservableDict, ObservableProxy)):
                # Register Variable's inner ObservableProxy in _nested_proxies so it gets
                # updated when this proxy's target is replaced (via _sync_from_target).
                # This is critical for State objects with Var[T] fields.
                if isinstance(inner_obs, ObservableProxy):
                    nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")
                    if name not in nested_proxies:
                        nested_proxies[name] = inner_obs
                return inner_obs  # pyright: ignore[reportUnknownVariableType]

        # For callables (methods, functions), return directly without wrapping
        if callable(value):
            return value  # type: ignore[return-value]

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

    def _is_atomic_value(self, value: Any) -> bool:
        """Check if value should be treated atomically (not wrapped in nested proxy).

        Atomic values include primitives and Enum instances. These values go through
        field Observables for proper change tracking and binding notifications.
        """
        from enum import Enum

        return _is_primitive(value) or isinstance(value, Enum)

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """Set a field value."""
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        target = object.__getattribute__(self, "_target")

        # For primitives and Enum, go through an Observable to track dirty state properly
        # and ensure bindings get notified of changes
        if self._is_atomic_value(value):
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
