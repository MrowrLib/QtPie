"""Setting - Variable with QSettings persistence."""

import types
from typing import Any

from observant import AnyObservable

from .variable import Variable


class Setting[T, W = None](Variable[T, W]):
    """Variable with QSettings persistence.

    Inherits EVERYTHING from Variable - just adds persistence callback.
    Auto-saves to QSettings on any change (value set, list append, dict update, etc.).

    Usage:
        @widget
        class MyApp(Widget):
            # Auto key: "MyApp:window_width", default 800
            window_width: Setting[int] = new(800)

            # Explicit group: "window:height"
            height: Setting[int] = new(600, group="window")

            # With widget: Setting[str, QLineEdit]
            username: Setting[str, QLineEdit] = new("")
    """

    _key: str
    _type_hint: type[T] | types.UnionType | None

    def __init__(
        self,
        wrapper: AnyObservable[T],
        *,
        key: str,
        type_hint: type[T] | types.UnionType | None = None,
        widget_type: type | None = None,
    ) -> None:
        super().__init__(wrapper, widget_type=widget_type)
        object.__setattr__(self, "_key", key)
        object.__setattr__(self, "_type_hint", type_hint)

        # Auto-save on ANY change (value set, list append, dict update, etc.)
        self._wrapper.on_change(self._persist)

    def _persist(self, *args: Any) -> None:
        """Save current value to QSettings."""
        from .settings_backend import get_settings_backend

        backend = get_settings_backend()
        backend.set(self._key, self.value, self._type_hint)

    @property
    def key(self) -> str:
        """Get the QSettings key for this setting."""
        return self._key
