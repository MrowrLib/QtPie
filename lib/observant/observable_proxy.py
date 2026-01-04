"""ObservableProxy - A reactive wrapper for any object."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, override

from .observable import Observable
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

    def __init__(self, target: T, *, dirty_tracking: bool = True) -> None:
        # Use object.__setattr__ to bypass our __setattr__
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_field_observables", {})
        object.__setattr__(self, "_field_lists", {})
        object.__setattr__(self, "_field_dicts", {})
        object.__setattr__(self, "_nested_proxies", {})
        object.__setattr__(self, "_callbacks", [])
        object.__setattr__(self, "_dirty_tracking", dirty_tracking)
        object.__setattr__(
            self,
            "_is_dirty",
            Observable[bool](False, dirty_tracking=False) if dirty_tracking else None,
        )

    def _get_or_create_field_observable(self, name: str) -> Observable[Any]:
        """Get or create an Observable for a field."""
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")

        if name not in field_observables:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")

            obs = Observable[Any](value, dirty_tracking=dirty_tracking)

            # When this field changes, update the target and notify
            def on_field_change(new_value: Any, field_name: str = name) -> None:
                target = object.__getattribute__(self, "_target")
                setattr(target, field_name, new_value)
                self._update_dirty_state()  # Update dirty state first
                self._notify_change()  # Then notify (so parent sees us as dirty)

            obs.on_change(on_field_change)
            field_observables[name] = obs

        return field_observables[name]

    def _get_or_create_field_list(self, name: str) -> ObservableList[Any]:
        """Get or create an ObservableList for a list field."""
        field_lists: dict[str, ObservableList[Any]] = object.__getattribute__(self, "_field_lists")

        if name not in field_lists:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")

            obs_list = ObservableList[Any](value, dirty_tracking=dirty_tracking)

            # When list changes, update the target and notify
            def on_list_change(field_name: str = name) -> None:
                target = object.__getattribute__(self, "_target")
                setattr(target, field_name, obs_list.to_list())
                self._update_dirty_state()
                self._notify_change()

            obs_list.on_change(on_list_change)
            field_lists[name] = obs_list

        return field_lists[name]

    def _get_or_create_field_dict(self, name: str) -> ObservableDict[Any, Any]:
        """Get or create an ObservableDict for a dict field."""
        field_dicts: dict[str, ObservableDict[Any, Any]] = object.__getattribute__(self, "_field_dicts")

        if name not in field_dicts:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")

            obs_dict = ObservableDict[Any, Any](value, dirty_tracking=dirty_tracking)

            # When dict changes, update the target and notify
            def on_dict_change(field_name: str = name) -> None:
                target = object.__getattribute__(self, "_target")
                setattr(target, field_name, obs_dict.to_dict())
                self._update_dirty_state()
                self._notify_change()

            obs_dict.on_change(on_dict_change)
            field_dicts[name] = obs_dict

        return field_dicts[name]

    def _get_or_create_nested_proxy(self, name: str) -> ObservableProxy[Any]:
        """Get or create a nested ObservableProxy for a complex field."""
        nested_proxies: dict[str, ObservableProxy[Any]] = object.__getattribute__(self, "_nested_proxies")

        if name not in nested_proxies:
            target = object.__getattribute__(self, "_target")
            value = getattr(target, name)
            dirty_tracking = object.__getattribute__(self, "_dirty_tracking")

            proxy = ObservableProxy[Any](value, dirty_tracking=dirty_tracking)

            # When nested proxy changes, propagate up
            def on_nested_change() -> None:
                self._update_dirty_state()  # Update dirty state first
                self._notify_change()  # Then notify

            proxy.on_change(on_nested_change)
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

    def unwrap(self) -> T:
        """Get the underlying target object."""
        return object.__getattribute__(self, "_target")

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

        # Check if we have an existing Observable for this field
        field_observables: dict[str, Observable[Any]] = object.__getattribute__(self, "_field_observables")

        if name in field_observables:
            # Update through the Observable
            field_observables[name].set(value)
        else:
            # Set directly on target and notify
            setattr(target, name, value)
            self._update_dirty_state()
            self._notify_change()

    @override
    def __repr__(self) -> str:
        target = object.__getattribute__(self, "_target")
        return f"ObservableProxy({target!r})"
