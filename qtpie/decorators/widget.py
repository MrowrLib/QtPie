from dataclasses import dataclass
from typing import TypeVar, cast

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform

T = TypeVar("T", bound=type)


@dataclass_transform()
def widget(cls: T) -> T:
    """Decorator that makes a class a dataclass with Qt widget capabilities."""
    return cast(T, dataclass(cls))
