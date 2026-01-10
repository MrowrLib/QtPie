# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Shared state and view model logic for Widget and Window."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from observant import Observable

if TYPE_CHECKING:
    from .variable import RecordVariable, Variable


class HasQtPieConfig(Protocol):
    """Protocol for Widget/Window with _qtpie_config."""

    _qtpie_config: Any


class QtPieStateBase:
    """Base state with dirty tracking and validation."""

    __slots__ = (
        "_host",
        "variables",
        "_was_dirty",
        "_record",
        "_was_valid",
        "_check_valid",
        "_aggregated_validation_errors",
        "_aggregated_is_valid",
        "_aggregated_is_dirty",
    )

    def __init__(self, host: Any) -> None:
        self._host = host
        self.variables: dict[str, Variable[Any]] = {}
        self._was_dirty: bool = False
        self._record: RecordVariable[Any] | None = None
        self._was_valid: bool = True
        self._check_valid: Callable[[bool], None] | None = None
        self._aggregated_validation_errors: Observable[list[str]] | None = None
        self._aggregated_is_valid: Observable[bool] | None = None
        self._aggregated_is_dirty: Observable[bool] | None = None

    # -------------------------------------------------------------------------
    # Dirty tracking
    # -------------------------------------------------------------------------

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any Variable has changed from its clean state. Returns Observable[bool] for reactive bindings."""
        if self._aggregated_is_dirty is None:
            self._aggregated_is_dirty = Observable[bool](False, dirty_tracking=False, validation=False)
            self._setup_is_dirty_aggregation()
        return self._aggregated_is_dirty

    def _compute_is_dirty(self) -> bool:
        """Compute the aggregated dirty state."""
        return any(var.is_dirty.get() for var in self.variables.values())

    def _setup_is_dirty_aggregation(self) -> None:
        """Subscribe to all Variables' is_dirty and aggregate."""

        def update_aggregated(_: Any = None) -> None:
            assert self._aggregated_is_dirty is not None
            self._aggregated_is_dirty.set(self._compute_is_dirty())

        # Subscribe to existing variables
        for var in self.variables.values():
            var.is_dirty.on_change(update_aggregated)

        # Initial update
        update_aggregated()

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed (Variables + record fields)."""
        # Exclude "record" from variables - we handle it specially below
        result = {name for name, var in self.variables.items() if name != "record" and var.is_dirty.get()}
        # Include record dirty fields (prefixed with "record.")
        if self._record is not None:
            for field_name in self._record.dirty_fields:
                result.add(f"record.{field_name}")
        return result

    def reset_dirty(self) -> None:
        """Mark all Variables as clean."""
        for var in self.variables.values():
            var.reset_dirty()

    @property
    def record_state(self) -> RecordVariable[Any] | Variable[Any]:
        """Access the RecordVariable/Variable wrapper for .is_dirty, .value, .observable."""
        # If we have a RecordVariable already, return it
        if self._record is not None:
            return self._record

        # Trigger access to create/register the record
        _ = self._host.record

        # Check if it's now a RecordVariable (auto-created)
        if self._record is not None:
            return self._record

        # Otherwise it's an explicit Variable declaration
        if "record" in self.variables:
            return self.variables["record"]

        raise TypeError(f"{type(self._host).__name__} has no record. Use Widget[YourModel] to enable record access.")

    def enable_dirty_hook(self) -> None:
        """Enable the on_dirty_changed hook (called after __setup__)."""

        def check_dirty_transition(is_now_dirty: bool) -> None:
            if self._was_dirty != is_now_dirty:
                self._was_dirty = is_now_dirty
                hook = getattr(self._host, "on_dirty_changed", None)
                if hook is not None:
                    hook(is_now_dirty)

        # Subscribe to the aggregated is_dirty Observable (not individual variables)
        # This ensures the hook fires after all variable changes are aggregated
        self.is_dirty.on_change(check_dirty_transition)

    def register_variable(self, name: str, var: Variable[Any] | RecordVariable[Any]) -> None:
        """Register a Variable and wire up dirty/valid hooks if enabled."""
        self.variables[name] = var  # type: ignore[assignment]
        if self._check_valid is not None:
            var.is_valid.on_change(self._check_valid)
        # Subscribe to validation/dirty aggregation if active
        self._subscribe_variable_to_aggregation(var)  # type: ignore[arg-type]

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all Variables are valid. Returns Observable[bool] for reactive bindings."""
        if self._aggregated_is_valid is None:
            self._aggregated_is_valid = Observable[bool](True, dirty_tracking=False, validation=False)
            self._setup_is_valid_aggregation()
        return self._aggregated_is_valid

    def _compute_is_valid(self) -> bool:
        """Compute the aggregated validity state."""
        return all(var.is_valid.get() for var in self.variables.values())

    def _setup_is_valid_aggregation(self) -> None:
        """Subscribe to all Variables' is_valid and aggregate."""

        def update_aggregated(_: Any = None) -> None:
            assert self._aggregated_is_valid is not None
            self._aggregated_is_valid.set(self._compute_is_valid())

        # Subscribe to existing variables
        for var in self.variables.values():
            var.is_valid.on_change(update_aggregated)

        # Initial update
        update_aggregated()

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Get validation errors: {field: {validator: [errors]}}."""
        result = {
            name: var.validation_errors.get()
            for name, var in self.variables.items()
            if var.validation_error_messages.get()  # only include fields with errors
        }
        # Include record validation errors under "record" key
        if self._record is not None:
            record_errors = self._record.validation_errors.get()
            if record_errors:
                result["record"] = record_errors
        return result

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Aggregated validation errors from all Variables. Reactive/bindable."""
        if self._aggregated_validation_errors is None:
            self._aggregated_validation_errors = Observable[list[str]]([], dirty_tracking=False, validation=False)
            self._setup_validation_aggregation()
        return self._aggregated_validation_errors

    def _setup_validation_aggregation(self) -> None:
        """Subscribe to all Variables' and record's validation_error_messages and aggregate."""

        def update_aggregated(_: Any = None) -> None:
            msgs: list[str] = []
            for var in self.variables.values():
                msgs.extend(var.validation_error_messages.get())
            # Include record validation errors
            if self._record is not None:
                msgs.extend(self._record.validation_error_messages.get())
            assert self._aggregated_validation_errors is not None
            self._aggregated_validation_errors.set(msgs)

        # Subscribe to existing variables
        for var in self.variables.values():
            var.validation_error_messages.on_change(update_aggregated)

        # Subscribe to record if present
        if self._record is not None:
            self._record.validation_error_messages.on_change(update_aggregated)

        # Initial update
        update_aggregated()

    def _subscribe_variable_to_aggregation(self, var: Variable[Any]) -> None:
        """Subscribe a new variable to the aggregation (if active)."""
        # Subscribe to validation error messages aggregation
        if self._aggregated_validation_errors is not None:

            def update_error_msgs(_: Any = None) -> None:
                msgs: list[str] = []
                for v in self.variables.values():
                    msgs.extend(v.validation_error_messages.get())
                # Include record validation errors
                if self._record is not None:
                    msgs.extend(self._record.validation_error_messages.get())
                assert self._aggregated_validation_errors is not None
                self._aggregated_validation_errors.set(msgs)

            var.validation_error_messages.on_change(update_error_msgs)
            update_error_msgs()

        # Subscribe to is_valid aggregation
        if self._aggregated_is_valid is not None:

            def update_is_valid(_: Any = None) -> None:
                assert self._aggregated_is_valid is not None
                self._aggregated_is_valid.set(self._compute_is_valid())

            var.is_valid.on_change(update_is_valid)
            update_is_valid()

        # Subscribe to is_dirty aggregation
        if self._aggregated_is_dirty is not None:

            def update_is_dirty(_: Any = None) -> None:
                assert self._aggregated_is_dirty is not None
                self._aggregated_is_dirty.set(self._compute_is_dirty())

            var.is_dirty.on_change(update_is_dirty)
            update_is_dirty()

    def enable_valid_hook(self) -> None:
        """Enable the on_valid_changed hook (called after __setup__)."""

        def check_valid_transition(_: bool) -> None:
            is_now_valid = self.is_valid.get()
            if self._was_valid != is_now_valid:
                self._was_valid = is_now_valid
                hook = getattr(self._host, "on_valid_changed", None)
                if hook is not None:
                    hook(is_now_valid)

        self._check_valid = check_valid_transition

        # Sync _was_valid with current state (after __setup__ ran and added validators)
        self._was_valid = self.is_valid.get()

        # Subscribe to each variable's is_valid
        for var in self.variables.values():
            var.is_valid.on_change(check_valid_transition)

    def add_validator(self, field: str, name: str, validator: Callable[[Any], None | str | list[str]]) -> None:
        """Add named validator to a specific field."""
        # Check if field is already in variables
        if field in self.variables:
            self.variables[field].add_validator(name, validator)
            return

        # Try to trigger variable creation by accessing it on the host
        if hasattr(self._host, field):
            attr = getattr(self._host, field)
            # After access, check if it's now registered
            if field in self.variables:
                self.variables[field].add_validator(name, validator)
                return
            # If it's a Variable directly
            if hasattr(attr, "add_validator"):
                attr.add_validator(name, validator)
                return

        # Check if it's a record field
        if self._record is None and hasattr(self._host, "record"):
            try:
                _ = self._host.record  # Trigger record creation
            except TypeError:
                pass  # No record type configured

        if self._record is not None:
            try:
                field_obs = getattr(self._record.observable, field)
                field_obs.add_validator(name, validator)
                return
            except AttributeError:
                pass

        raise KeyError(f"No field named '{field}' found")


class QtPieViewModelBase:
    """Base view model with dirty tracking and validation."""

    __slots__ = ("_state",)

    def __init__(self, state: QtPieStateBase) -> None:
        self._state = state

    # -------------------------------------------------------------------------
    # Dirty tracking
    # -------------------------------------------------------------------------

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any Variable has changed from its clean state. Returns Observable[bool] for reactive bindings."""
        return self._state.is_dirty

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        return self._state.dirty_fields

    def reset_dirty(self) -> None:
        """Mark all Variables as clean."""
        self._state.reset_dirty()

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all Variables are valid. Returns Observable[bool] for reactive bindings."""
        return self._state.is_valid

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Get validation errors: {field: {validator: [errors]}}."""
        return self._state.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Aggregated validation errors from all Variables. Reactive/bindable."""
        return self._state.validation_error_messages


class QtPieState(QtPieStateBase):
    """Instance-level QtPie state for Widget/Window."""

    __slots__ = ("_view_model", "_widget_is_dirty", "_widget_is_valid")

    def __init__(self, host: Any) -> None:
        super().__init__(host)
        self._view_model: QtPieViewModel | None = None
        self._widget_is_dirty: Observable[bool] | None = None
        self._widget_is_valid: Observable[bool] | None = None

    @property
    def view_model(self) -> QtPieViewModel:
        if self._view_model is None:
            self._view_model = QtPieViewModel(self)
        return self._view_model

    # -------------------------------------------------------------------------
    # Widget-level aggregation (includes record if present)
    # -------------------------------------------------------------------------

    @property
    def widget_is_dirty(self) -> Observable[bool]:
        """Widget-level dirty state: aggregates Variables AND record (if present)."""
        if self._widget_is_dirty is None:
            self._widget_is_dirty = Observable[bool](False, dirty_tracking=False, validation=False)
            self._setup_widget_is_dirty()
        return self._widget_is_dirty

    def _compute_widget_is_dirty(self) -> bool:
        """Compute widget-level dirty: Variables OR record is dirty."""
        # Check Variables via view_model
        if self.is_dirty.get():
            return True
        # Check record if present
        if self._record is not None:
            return self._record.is_dirty.get()
        return False

    def _setup_widget_is_dirty(self) -> None:
        """Subscribe to view_model.is_dirty and record.is_dirty."""

        def update_widget_dirty(_: Any = None) -> None:
            assert self._widget_is_dirty is not None
            self._widget_is_dirty.set(self._compute_widget_is_dirty())

        # Subscribe to view_model (Variables) dirty state
        self.is_dirty.on_change(update_widget_dirty)

        # Subscribe to record if present
        if self._record is not None:
            self._record.is_dirty.on_change(update_widget_dirty)

        # Initial update
        update_widget_dirty()

    def _subscribe_record_to_widget_dirty(self) -> None:
        """Subscribe record to widget-level dirty aggregation (called when record is created)."""
        if self._widget_is_dirty is not None and self._record is not None:

            def update_widget_dirty(_: Any = None) -> None:
                assert self._widget_is_dirty is not None
                self._widget_is_dirty.set(self._compute_widget_is_dirty())

            self._record.is_dirty.on_change(update_widget_dirty)
            update_widget_dirty()

    @property
    def widget_is_valid(self) -> Observable[bool]:
        """Widget-level validity: aggregates Variables AND record (if present)."""
        if self._widget_is_valid is None:
            self._widget_is_valid = Observable[bool](True, dirty_tracking=False, validation=False)
            self._setup_widget_is_valid()
        return self._widget_is_valid

    def _compute_widget_is_valid(self) -> bool:
        """Compute widget-level validity: Variables AND record are valid."""
        # Check Variables via view_model
        if not self.is_valid.get():
            return False
        # Check record if present
        if self._record is not None:
            return self._record.is_valid.get()
        return True

    def _setup_widget_is_valid(self) -> None:
        """Subscribe to view_model.is_valid and record.is_valid."""

        def update_widget_valid(_: Any = None) -> None:
            assert self._widget_is_valid is not None
            self._widget_is_valid.set(self._compute_widget_is_valid())

        # Subscribe to view_model (Variables) validity state
        self.is_valid.on_change(update_widget_valid)

        # Subscribe to record if present
        if self._record is not None:
            self._record.is_valid.on_change(update_widget_valid)

        # Initial update
        update_widget_valid()

    def _subscribe_record_to_widget_valid(self) -> None:
        """Subscribe record to widget-level validity aggregation (called when record is created)."""
        if self._widget_is_valid is not None and self._record is not None:

            def update_widget_valid(_: Any = None) -> None:
                assert self._widget_is_valid is not None
                self._widget_is_valid.set(self._compute_widget_is_valid())

            self._record.is_valid.on_change(update_widget_valid)
            update_widget_valid()


class QtPieViewModel(QtPieViewModelBase):
    """Auto-generated view model containing only Variable fields."""

    def __init__(self, state: QtPieState) -> None:
        super().__init__(state)

    def __getattr__(self, name: str) -> Variable[Any]:
        # Get variable names from class config
        if name in type(self._state._host)._qtpie_config.variable_names:
            return getattr(self._state._host, name)
        raise AttributeError(f"ViewModel has no attribute {name!r}")
