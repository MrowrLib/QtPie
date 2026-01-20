# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""WidgetBase - Mixin that adds QtPie features to any widget."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast, get_args, get_origin, overload

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
            # Setting a value - reuse existing proxy to preserve subscriptions
            from observant import ObservableProxy

            existing_record = obj._qtpie._record
            if existing_record is not None:
                # Use replace_target to update the existing proxy in-place.
                # This preserves all subscriptions set up by bindings.
                existing_record.observable.replace_target(value)  # pyright: ignore[reportAttributeAccessIssue]
            else:
                # First time - create new proxy
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

        # Auto-new bare annotations (non-Variable types)
        _auto_new_bare_annotations(cls)

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

        @property
        def record_value(self) -> T:
            """Get the raw record value, unwrapped from the ObservableProxy.

            Use this when you need the actual object (e.g., for isinstance checks):
                if isinstance(self.record_value.auth, ApiKeyAuth):
                    ...
            """
            ...

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        def __getattr__(self, name: str) -> Any:
            """Handle attribute access for special cases."""
            if name == "record":
                # Use AttributeError so hasattr() works correctly
                raise AttributeError(f"{type(self).__name__} has no record type. Use WidgetBase[YourModel] to enable record access.")
            if name == "record_value":
                # Return unwrapped record value if available
                if hasattr(self, "_qtpie") and self._qtpie._record is not None:
                    return self._qtpie._record.value
                raise AttributeError(f"{type(self).__name__} has no record type. Use WidgetBase[YourModel] to enable record_value access.")
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
    # Signal Resolution
    # -------------------------------------------------------------------------

    def signal(self, name: str) -> Any:
        """Get a signal by name, searching up the parent hierarchy.

        First checks this widget, then walks up parent() chain, then QApplication.

        Args:
            name: The signal name (e.g., "on_reload_window")

        Returns:
            The signal if found

        Raises:
            AttributeError: If signal not found in hierarchy

        Example:
            self.signal("on_reload_window").emit()
        """
        from .utils.common import is_signal, resolve_signal_from_hierarchy

        # First check on self
        target = getattr(self, name, None)
        if target is not None and is_signal(target):
            return target

        # Search up hierarchy
        target = resolve_signal_from_hierarchy(self, name)
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

    # fmt: off
    # var() overloads for type inference
    @overload
    def var(self, name: str) -> Any: ...
    @overload
    def var[T1](self, name: str, t1: type[T1]) -> T1: ...
    @overload
    def var[T1, T2](self, name: str, t1: type[T1], t2: type[T2]) -> T1 | T2: ...
    @overload
    def var[T1, T2, T3](self, name: str, t1: type[T1], t2: type[T2], t3: type[T3]) -> T1 | T2 | T3: ...
    @overload
    def var[T1, T2, T3, T4](self, name: str, t1: type[T1], t2: type[T2], t3: type[T3], t4: type[T4]) -> T1 | T2 | T3 | T4: ...
    # With None
    @overload
    def var[T1](self, name: str, t1: type[T1], t2: None) -> T1 | None: ...
    @overload
    def var[T1, T2](self, name: str, t1: type[T1], t2: type[T2], t3: None) -> T1 | T2 | None: ...
    @overload
    def var[T1, T2, T3](self, name: str, t1: type[T1], t2: type[T2], t3: type[T3], t4: None) -> T1 | T2 | T3 | None: ...
    # fmt: on
    def var(self, name: str, *types: type[Any] | None) -> Any:  # pyright: ignore[reportInconsistentOverload]
        """Resolve a variable by name from the binding context.

        Searches in this order:
        1. This widget (with and without underscore prefix)
        2. Parent widget hierarchy (walking up parent() chain)
        3. QApplication.instance() for app-level Variables

        Args:
            name: The variable name to resolve (e.g., "count" or "_count").
            *types: Optional type(s) for type inference. Pass None as last arg for optional.

        Returns:
            The resolved value (unwrapped from Variable if applicable).

        Raises:
            AttributeError: If variable not found in context or parent hierarchy.

        Example:
            x = self.var("count")  # Returns Any
            x = self.var("count", int)  # Returns int
            x = self.var("pet", Dog, Cat)  # Returns Dog | Cat
            x = self.var("pet", Dog, None)  # Returns Dog | None
        """
        from qtpie.bindings.expression import resolve_var

        return resolve_var(self, name)

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


def _auto_record_bind_children(cls: type) -> None:  # pyright: ignore[reportUnusedFunction] - imported in widget.py
    """Auto-bind record for child Widget[T] fields where T matches parent's T.

    When a parent Widget[T] contains a child Widget[T] field (same T),
    automatically set field.bind = "record" so the child inherits the parent's record.

    This must be called AFTER __init_subclass__ has set up _qtpie_config
    because NewField.__set_name__ runs before the config exists.

    Opt-out: Use bind=False on the child field to skip auto-binding.
    """
    from .new_field import NewField

    config = getattr(cls, "_qtpie_config", None)
    if config is None:
        return

    parent_record_type = getattr(config, "record_type", None)
    if parent_record_type is None:
        return  # Parent doesn't have a record type

    # Check each field for matching record types
    for _name, field in config.fields.items():
        if not isinstance(field, NewField):
            continue

        # Skip if already has explicit bind (including bind=False opt-out)
        if field.bind is not None:
            continue

        # Get child's record type
        child_cls = field.field_type
        if child_cls is None:
            continue

        child_config = getattr(child_cls, "_qtpie_config", None)
        if child_config is None:
            continue

        child_record_type = getattr(child_config, "record_type", None)
        if child_record_type is None:
            continue

        # If types match, auto-bind record
        if parent_record_type == child_record_type:
            field.bind = "record"


def _auto_new_bare_annotations(cls: type) -> None:
    """Convert bare type annotations to NewField instances.

    This enables the shorthand syntax:
        _label: QLabel           # Auto: creates QLabel()
        _label: QLabel = new()   # Explicit: also creates QLabel()
        _label: QLabel = none()  # Opt-out: no instance created

    Skip:
    - Variable types (have special bare handling as required bindings)
    - Already has = new() (in config.fields)
    - Has = none() (opt-out sentinel)
    - list[T], dict[K,V], set[T] (handled by repeaters)
    """
    from .menu import Section, Separator
    from .new import _NONE_SENTINEL
    from .variable import Variable

    config = cls._qtpie_config  # type: ignore[attr-defined]
    annotations = getattr(cls, "__annotations__", {})

    # First pass: remove none() sentinels from the class
    # Track which names had sentinels so we skip them in second pass
    sentinel_names: set[str] = set()
    for name in list(annotations.keys()):
        class_value = cls.__dict__.get(name)
        if class_value is _NONE_SENTINEL:
            delattr(cls, name)
            sentinel_names.add(name)

    # Second pass: auto-new bare annotations
    for name, annotation in annotations.items():
        # Skip if had none() sentinel (opt-out)
        if name in sentinel_names:
            continue

        # Skip if already processed (has = new())
        if name in config.fields:
            continue

        # Skip if already a variable name (bare Variable[T])
        if name in config.variable_names:
            continue

        # Skip if it's in required_bindings (bare Variable[T])
        if name in config.required_bindings:
            continue

        # Get the raw annotation to check for generics
        origin = get_origin(annotation)

        # Skip Variables - have their own bare handling
        # Also handle string annotations from 'from __future__ import annotations'
        if origin is Variable or annotation is Variable:
            continue
        if isinstance(annotation, str) and (annotation.startswith("Variable[") or annotation == "Variable"):
            continue

        # Skip list/dict/set - handled by repeaters
        if origin in (list, dict, set):
            continue

        # Skip menu marker types (Separator, Section) - handled by @menu
        if annotation is Separator or annotation is Section:
            continue

        # Skip if there's any value assigned (not bare)
        if name in cls.__dict__:
            continue

        # Skip special names that shouldn't be auto-instantiated
        if name in ("record", "_qtpie", "_qtpie_config"):
            continue

        # Create auto NewField (no args) and let __set_name__ handle type detection
        new_field = NewField()
        # Set on class FIRST so __set_name__ can find it in __dict__
        setattr(cls, name, new_field)
        # Now call __set_name__ to do type detection
        new_field.__set_name__(cls, name)
        config.fields[name] = new_field
