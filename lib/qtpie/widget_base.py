# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""WidgetBase - Mixin that adds QtPie features to any widget."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar, cast, get_args, get_origin

from observant import Observable

from .new_field import NewField
from .new_fields import new_fields
from .qtpie_config import _QtPieConfig
from .state import QtPieState
from .variable import NO_DEFAULT, RecordVariable, Variable, _create_observable_for_type, _RequiredBindingDescriptor, _VariableDescriptor


class _RecordDescriptor[T]:
    """Descriptor for auto-created record on WidgetBase[T].

    This is used when the user doesn't explicitly declare `record: Variable[T] = new(...)`.
    It lazily creates the record Variable on first access.
    """

    def __init__(self, record_type: type[T]) -> None:
        self._record_type = record_type

    def __get__(self, obj: WidgetBase[T] | None, objtype: type | None = None) -> RecordVariable[T]:
        if obj is None:
            return self  # type: ignore[return-value]

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        state = obj._qtpie
        if state._record is None:
            from observant import ObservableProxy

            try:
                wrapper = _create_observable_for_type(self._record_type, NO_DEFAULT)
            except ValueError:
                # Type requires constructor args - create proxy with None target
                # User must set it in __setup__ or later
                wrapper = ObservableProxy[T](None)  # type: ignore[arg-type]
            record_var = RecordVariable(cast(ObservableProxy[T], wrapper))
            state._record = record_var
            state.register_variable("record", record_var)
            # Subscribe record to widget-level aggregation if active
            state._subscribe_record_to_widget_dirty()
            state._subscribe_record_to_widget_valid()

        return state._record  # type: ignore[return-value]

    def __set__(self, obj: WidgetBase[T], value: T | RecordVariable[T]) -> None:
        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        if isinstance(value, RecordVariable):
            obj._qtpie._record = value
            obj._qtpie.register_variable("record", value)  # type: ignore[arg-type]
        else:
            # Setting a value - always create a new ObservableProxy with the value
            from observant import ObservableProxy

            wrapper = ObservableProxy(value)
            record_var = RecordVariable(wrapper)
            obj._qtpie._record = record_var
            obj._qtpie.register_variable("record", record_var)

        # Subscribe record to widget-level aggregation if active
        obj._qtpie._subscribe_record_to_widget_dirty()
        obj._qtpie._subscribe_record_to_widget_valid()


class WidgetBase[T = None]:
    """Mixin that adds QtPie reactive features to any Qt widget.

    Use this when subclassing existing Qt widgets like QListView, QTableView, etc.

    Usage:
        @widget
        class MyListView(QListView, WidgetBase):
            _items: Variable[list[str]] = new([])

            def __setup__(self):
                # Called after Qt's __init__ completes
                self._items = ["first", "second"]

    With record type:
        @widget
        class PersonListView(QListView, WidgetBase[Person]):
            def __setup__(self):
                self.record = Person("Alice", 30)

    Features:
        - Works with @widget decorator (required for full functionality)
        - Supports WidgetBase[T] for record types (like Widget[T])
        - Auto-creates _qtpie_config for compatibility with Widget
        - Variable fields work automatically
        - __setup__ lifecycle hook
        - Validation and dirty tracking
    """

    # Class-level config (set up in __init_subclass__)
    _qtpie_config: _QtPieConfig
    # Instance-level state (set during __init__)
    _qtpie: QtPieState

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Create fresh config for this subclass (mirrors Widget.__init_subclass__)
        cls._qtpie_config = _QtPieConfig()

        # Extract T from WidgetBase[T] or SomeSubclass[T] if present
        # Skip if T is still a TypeVar (unparameterized generic)
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            # Check if origin is WidgetBase or a subclass of WidgetBase
            if origin is not None and isinstance(origin, type) and issubclass(origin, WidgetBase):
                args = get_args(base)
                if args and not isinstance(args[0], TypeVar):
                    cls._qtpie_config.record_type = args[0]
                break

        # Check if user declared 'record' explicitly
        has_explicit_record = "record" in cls.__dict__

        # Collect fields and variable names
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, NewField):
                cls._qtpie_config.fields[name] = value
            elif isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # Detect bare Variable[T] annotations (required bindings)
        _detect_required_bindings(cls)

        # Apply @new_fields to handle non-Variable instantiation
        new_fields(cls)

        # Auto-create record descriptor if WidgetBase[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        # Runtime: _RecordDescriptor returns RecordVariable which forwards via __getattr__
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        def __getattr__(self, name: str) -> NoReturn:
            """Handle attribute access for special cases."""
            if name == "record":
                # Use AttributeError so hasattr() works correctly
                raise AttributeError(f"{type(self).__name__} has no record type. Use WidgetBase[YourModel] to enable record access.")
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, field: str, name: str, validator: Callable[[Any], None | str | list[str]]) -> None:
        """Add a named validator to a field.

        Usage:
            def __setup__(self) -> None:
                self.add_validator("name", "required", lambda v: None if v else "Required")
        """
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        self._qtpie.add_validator(field, name, validator)

    def remove_validator(self, field: str, name: str) -> None:
        """Remove a named validator from a field."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        self._qtpie.remove_validator(field, name)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any field has changed. Returns Observable[bool] for reactive bindings.

        Aggregates dirty state from Variables AND record (if present).
        """
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.widget_is_dirty

    def reset_dirty(self) -> None:
        """Mark all fields as clean (Variables and record)."""
        if not hasattr(self, "_qtpie"):
            return  # Nothing to reset
        # Reset Variables
        self._qtpie.reset_dirty()
        # Reset record if present
        if self._qtpie._record is not None:
            self._qtpie._record.reset_dirty()

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        if not hasattr(self, "_qtpie"):
            return set()
        return self._qtpie.dirty_fields

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all fields are valid. Returns Observable[bool] for reactive bindings.

        Aggregates validity from Variables AND record (if present).
        """
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.widget_is_valid

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Errors: {field: {validator: [errors]}}."""
        if not hasattr(self, "_qtpie"):
            return {}
        return self._qtpie.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Returns Observable[list[str]] for reactive bindings."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.validation_error_messages

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    def on_dirty_changed(self, is_dirty: bool) -> None:
        """Called when dirty state transitions (clean→dirty or dirty→clean).

        Override this to react to dirty state changes, e.g., enable/disable save button.

        Example:
            @widget
            class MyWidget(QWidget, WidgetBase):
                @override
                def on_dirty_changed(self, is_dirty: bool) -> None:
                    self._save_btn.setEnabled(is_dirty)
        """
        pass

    def on_valid_changed(self, is_valid: bool) -> None:
        """Called when validity state transitions (valid→invalid or invalid→valid).

        Override this to react to validation changes, e.g., show/hide error messages.

        Example:
            @widget
            class MyWidget(QWidget, WidgetBase):
                @override
                def on_valid_changed(self, is_valid: bool) -> None:
                    self._submit_btn.setEnabled(is_valid)
        """
        pass

    async def on_close(self) -> None:
        """Async hook called when the widget is closing.

        Override this to perform async cleanup before the widget closes.
        The close event is automatically accepted after this completes.

        Example:
            @widget
            class MyWidget(QWidget, WidgetBase):
                @override
                async def on_close(self) -> None:
                    await self.save_data()
        """
        pass


def _detect_required_bindings(cls: type) -> None:
    """Detect bare Variable[T] annotations as required bindings."""
    from .utils.common import detect_required_bindings

    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)
