# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Property resolution utilities shared across QtPie modules."""

from typing import Any

from observant import Observable, ObservableProxy


def resolve_nested_property(obj: Any, path: str) -> Any:
    """Resolve a dotted property path like 'breed.name' on an object."""
    parts = path.split(".")
    current: Any = obj
    for part in parts:
        if isinstance(current, Observable):
            current = current.get()
        if isinstance(current, ObservableProxy):
            prop_obs = getattr(current, part, None)
            if isinstance(prop_obs, Observable):
                current = prop_obs.get()
            else:
                current = prop_obs
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return f"<unknown:{path}>"
    if isinstance(current, Observable):
        current = current.get()
    return current
