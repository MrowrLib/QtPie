"""Shared base mixin for Widget, Window, and App.

This mixin provides the common API for:
- Validation (add_validator, remove_validator, is_valid, validation_errors, validation_error_messages)
- Dirty tracking (is_dirty, reset_dirty, dirty_fields)
- Signals (signal, emit_signal)
- Variable resolution (var)
- Lifecycle hooks (on_dirty_changed, on_valid_changed)
- Runtime widget building (build)
"""

# Note: __future__ annotations is needed here because this mixin references
# QtPieState in type annotations. Without it, get_type_hints() on subclasses
# fails with NameError because QtPieState isn't in the subclass's namespace.
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable

if TYPE_CHECKING:
    from qtpie.state import QtPieState


class QtPieComponentBase:
    """Mixin providing shared methods for Widget, Window, and App.

    This mixin requires:
    - self._qtpie: QtPieState (created lazily if not present)

    Note: We intentionally don't declare `_qtpie: QtPieState` here because
    get_type_hints() would fail to resolve it when called on subclasses.
    The concrete classes (Widget, Window, App) declare this attribute themselves.
    """

    def _ensure_state(self) -> QtPieState:
        """Ensure _qtpie state exists, creating it lazily if needed."""
        from qtpie.state import QtPieState

        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)  # type: ignore[arg-type]
        return self._qtpie

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, field: str, name: str, validator: Callable[[Any], None | str | list[str]]) -> None:
        """Add a named validator to a field.

        Usage:
            def __setup__(self) -> None:
                self.add_validator("name", "required", lambda v: None if v else "Required")
        """
        self._ensure_state().add_validator(field, name, validator)

    def remove_validator(self, field: str, name: str) -> None:
        """Remove a named validator from a field."""
        self._ensure_state().remove_validator(field, name)

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all fields are valid. Returns Observable[bool] for reactive bindings.

        Aggregates validity from Variables AND record (if present).
        """
        return self._ensure_state().widget_is_valid

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Errors: {field: {validator: [errors]}}."""
        if not hasattr(self, "_qtpie"):
            return {}
        return self._qtpie.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Returns Observable[list[str]] for reactive bindings."""
        return self._ensure_state().validation_error_messages

    # -------------------------------------------------------------------------
    # Dirty Tracking
    # -------------------------------------------------------------------------

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any field has changed. Returns Observable[bool] for reactive bindings.

        Aggregates dirty state from Variables AND record (if present).
        """
        return self._ensure_state().widget_is_dirty

    def reset_dirty(self) -> None:
        """Mark all fields as clean (Variables and record)."""
        if not hasattr(self, "_qtpie"):
            return  # Nothing to reset
        # Reset Variables
        self._qtpie.reset_dirty()
        # Reset record if present
        if self._qtpie._record is not None:  # pyright: ignore[reportPrivateUsage]
            self._qtpie._record.reset_dirty()  # pyright: ignore[reportPrivateUsage]

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        if not hasattr(self, "_qtpie"):
            return set()
        return self._qtpie.dirty_fields

    # -------------------------------------------------------------------------
    # Signal Resolution
    # -------------------------------------------------------------------------

    def signal(self, name: str) -> Any:
        """Get a signal by name, searching up the parent hierarchy.

        First checks this component, then walks up parent() chain, then QApplication.

        Args:
            name: The signal name (e.g., "on_reload_window")

        Returns:
            The signal if found

        Raises:
            AttributeError: If signal not found in hierarchy

        Example:
            self.signal("on_reload_window").emit()
        """
        from qtpie.utils.common import is_signal, resolve_signal_from_hierarchy

        # First check on self
        target = getattr(self, name, None)
        if target is not None and is_signal(target):
            return target

        # Search up hierarchy
        target = resolve_signal_from_hierarchy(self, name)  # type: ignore[arg-type]
        if target is not None and is_signal(target):
            return target

        raise AttributeError(f"Signal '{name}' not found on {type(self).__name__} or in parent hierarchy")

    def emit_signal(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Emit a signal by name, searching up the parent hierarchy.

        Convenience method that combines signal() lookup with emit().

        Args:
            name: The signal name (e.g., "on_reload_window")
            *args: Arguments to pass to signal.emit()
            **kwargs: Keyword arguments to pass to signal.emit()

        Raises:
            AttributeError: If signal not found in hierarchy

        Example:
            self.emit_signal("on_reload_window")
        """
        sig = self.signal(name)
        sig.emit(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Variable Resolution
    # -------------------------------------------------------------------------

    def var(self, name: str) -> Any:
        """Resolve a variable by name from the binding context.

        Searches in this order:
        1. This component (with and without underscore prefix)
        2. Parent widget hierarchy (walking up parent() chain)
        3. QApplication.instance() for app-level Variables

        Args:
            name: The variable name to resolve (e.g., "count" or "_count").

        Returns:
            The resolved value (unwrapped from Variable if applicable).

        Raises:
            AttributeError: If variable not found in context or parent hierarchy.

        Example:
            count = self.var("count")  # Gets current value of _count Variable
            item = self.var("selected_item")  # May resolve from parent widget
        """
        from qtpie.bindings.expression import resolve_var

        return resolve_var(self, name)  # type: ignore[arg-type]

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    def on_dirty_changed(self, is_dirty: bool) -> None:
        """Called when dirty state transitions (clean->dirty or dirty->clean).

        Override this to react to dirty state changes, e.g., enable/disable save button.

        Example:
            @widget
            class MyWidget(Widget):
                @override
                def on_dirty_changed(self, is_dirty: bool) -> None:
                    self._save_btn.setEnabled(is_dirty)
        """
        pass

    def on_valid_changed(self, is_valid: bool) -> None:
        """Called when validity state transitions (valid->invalid or invalid->valid).

        Override this to react to validation changes, e.g., show/hide error messages.

        Example:
            @widget
            class MyWidget(Widget):
                @override
                def on_valid_changed(self, is_valid: bool) -> None:
                    self._submit_btn.setEnabled(is_valid)
        """
        pass

    # -------------------------------------------------------------------------
    # Runtime Building
    # -------------------------------------------------------------------------

    def build[W](self, cls: type[W], /, *args: Any, **kwargs: Any) -> W:
        """Build an instance at runtime with new()-like signal and property wiring.

        This is the runtime equivalent of new(). Use it when you need to create
        widget instances dynamically (not at class definition time).

        Args:
            cls: The class to instantiate.
            *args: Positional arguments passed to the constructor.
            **kwargs: Keyword arguments. Signal names (e.g., clicked="handler")
                      are extracted and connected to methods on this component.

        Returns:
            The created instance with signals connected and properties applied.

        Supported (see create_instance for full details):
            - Signal connections: clicked="method_name" or clicked=lambda: ...
            - Widget props: enabled=False, toolTip="...", etc.
            - name=, classes=, bind=, visible=, enabled=, ref(), t()
            - Variable bindings for child widgets with required bindings (bare Variable[T])

        NOT supported (only work with new() at class definition time):
            - list/dict repeaters, label=, grid=, stretch=, layout hints

        Example:
            def on_add_item(self) -> None:
                new_item = self.build(ItemWidget, on_remove="on_remove_item")
                self.layout().addWidget(new_item)
        """
        from qtpie.create import create_instance

        return create_instance(self, cls, *args, **kwargs)  # type: ignore[arg-type]
