"""Settings backend - QSettings wrapper with type-aware serialization."""

import json
import logging
import types
from dataclasses import asdict, fields, is_dataclass
from enum import Enum
from typing import Any, get_args, get_origin

from qtpy.QtCore import QSettings

logger = logging.getLogger(__name__)


def _reconstruct_dataclass[T](data: dict[str, Any], cls: type[T]) -> T:
    """Recursively reconstruct a dataclass from a dict.

    Handles nested dataclasses and enums.
    """
    if not is_dataclass(cls):
        raise TypeError(f"Cannot reconstruct non-dataclass type: {cls}")

    kwargs: dict[str, Any] = {}
    for field in fields(cls):
        if field.name not in data:
            continue

        value = data[field.name]
        field_type = field.type

        # Handle string annotations (forward references)
        if isinstance(field_type, str):
            # Can't resolve string annotations easily, just use raw value
            kwargs[field.name] = value
            continue

        # Reconstruct the field value
        kwargs[field.name] = _reconstruct_value(value, field_type)

    return cls(**kwargs)


def _reconstruct_value(value: Any, type_hint: Any) -> Any:
    """Reconstruct a value based on its type hint."""
    if value is None:
        return None

    # Handle Union types (e.g., Dog | None)
    origin = get_origin(type_hint)
    if origin is types.UnionType:
        # Try each type in the union
        for arg in get_args(type_hint):
            if arg is type(None):
                continue
            try:
                return _reconstruct_value(value, arg)
            except (TypeError, ValueError):
                continue
        return value

    # Handle Enum
    if isinstance(type_hint, type) and issubclass(type_hint, Enum):
        return type_hint(value)

    # Handle nested dataclass - value may be dict or JSON string
    if is_dataclass(type_hint) and not isinstance(type_hint, type):  # pyright: ignore[reportUnknownArgumentType]
        pass  # Skip instances, only handle classes
    elif is_dataclass(type_hint):  # pyright: ignore[reportUnknownArgumentType]
        if isinstance(value, str):
            # JSON string - decode first
            value = json.loads(value)
        if isinstance(value, dict):
            return _reconstruct_dataclass(value, type_hint)  # pyright: ignore[reportArgumentType, reportUnknownVariableType, reportUnknownArgumentType]

    # Handle list[T]
    if origin is list:
        args = get_args(type_hint)
        if args and isinstance(value, list):
            item_type = args[0]
            return [_reconstruct_value(item, item_type) for item in value]  # pyright: ignore[reportUnknownVariableType]
        return value

    # Handle dict[K, V]
    if origin is dict:
        args = get_args(type_hint)
        if len(args) >= 2 and isinstance(value, dict):
            key_type, val_type = args[0], args[1]
            return {
                _reconstruct_value(k, key_type): _reconstruct_value(v, val_type)
                for k, v in value.items()  # pyright: ignore[reportUnknownVariableType]
            }
        return value

    # Handle primitive type coercion (QSettings may store as strings)
    if isinstance(type_hint, type):
        if type_hint is bool:
            # QSettings stores bools as strings on some platforms
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if type_hint is int and isinstance(value, str):
            return int(value)
        if type_hint is float and isinstance(value, str):
            return float(value)

    # Return as-is
    return value


class SettingsBackend:
    """QSettings wrapper with type-aware serialization."""

    # Sentinel for None values (since QSettings can't distinguish None from missing)
    _NONE_SENTINEL = "__QTPIE_NONE__"

    def __init__(self) -> None:
        """Initialize with QSettings using app's org/name."""
        self._qsettings = QSettings()

    def get[T](self, key: str, default: T, type_hint: type[T] | types.UnionType | None) -> T:
        """Load value from QSettings, deserialize if needed."""
        raw = self._qsettings.value(key)
        if raw is None:
            return default
        return self._deserialize(raw, type_hint, default)

    def set(self, key: str, value: Any, type_hint: type | types.UnionType | None) -> None:
        """Serialize and save to QSettings."""
        serialized = self._serialize(value)
        self._qsettings.setValue(key, serialized)

    def _serialize(self, value: Any) -> Any:
        """Convert value for QSettings storage."""
        if value is None:
            return self._NONE_SENTINEL

        if isinstance(value, Enum):
            return value.value

        if is_dataclass(value) and not isinstance(value, type):
            return json.dumps(asdict(value))

        if isinstance(value, list):
            return [self._serialize(item) for item in value]  # pyright: ignore[reportUnknownVariableType]

        if isinstance(value, dict):
            return {k: self._serialize(v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType]

        # QSettings handles primitives (str, int, float, bool)
        return value

    def _deserialize[T](self, raw: Any, type_hint: type[T] | types.UnionType | None, default: T) -> T:
        """Convert QSettings value back to typed value."""
        if raw == self._NONE_SENTINEL:
            return None  # type: ignore[return-value]

        if type_hint is None:
            return raw  # type: ignore[return-value]

        try:
            return _reconstruct_value(raw, type_hint)  # type: ignore[return-value]
        except (ValueError, TypeError, json.JSONDecodeError, KeyError, AttributeError) as e:
            # Type mismatch, corrupted data, etc. - fall back to default
            logger.warning(
                "Failed to deserialize setting (using default): %s. Raw value: %r, Expected type: %s",
                e,
                raw[:100] if isinstance(raw, str) and len(raw) > 100 else raw,
                type_hint,
            )
            return default

    def sync(self) -> None:
        """Force write to storage."""
        self._qsettings.sync()

    def clear(self) -> None:
        """Clear all settings (useful for testing)."""
        self._qsettings.clear()


# Module-level singleton
_backend: SettingsBackend | None = None


def get_settings_backend() -> SettingsBackend:
    """Get the global settings backend (lazy init)."""
    global _backend
    if _backend is None:
        _backend = SettingsBackend()
    return _backend


def reset_settings_backend() -> None:
    """Reset the global settings backend (for testing)."""
    global _backend
    if _backend is not None:
        _backend.clear()
        _backend.sync()
    _backend = None
