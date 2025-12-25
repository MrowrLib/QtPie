"""Widget base class - optional mixin with record binding support."""

from collections.abc import Callable
from typing import Any, cast, get_args, get_origin

from observant import ObservableProxy
from qtpy.QtWidgets import QWidget

from qtpie.styles.loader import load_stylesheet as _load_stylesheet


class Widget[T = None]:
    """
    Base class for widgets with optional record binding.

    Widget can be used in two ways:

    1. **Without type parameter** - Just a mixin, no record binding:
       ```python
       @widget()
       class SimpleWidget(QWidget, Widget):
           label: QLabel = make(QLabel, "Hello")
       ```

    2. **With type parameter** - Enables automatic record binding:
       ```python
       @widget()
       class DogEditor(QWidget, Widget[Dog]):
           name: QLineEdit = make(QLineEdit)  # auto-binds to record.name
           age: QSpinBox = make(QSpinBox)      # auto-binds to record.age
       ```

    When a type parameter is provided:
    - Record is auto-created as `T()` by default
    - Custom record via `record: Dog = make(Dog, name="Buddy")`
    - Manual setup via `record: Dog = make_later()` + set in `setup()`
    - `ObservableProxy` is auto-created wrapping the record
    - Widget fields auto-bind to record properties by matching names
    """

    # Type hints for IDE - actual fields are created by @widget decorator
    record: T
    record_observable_proxy: ObservableProxy[T]

    def set_record(self, record: T) -> None:
        """
        Set a new record and rebind all widgets.

        This allows changing the record after widget creation.
        """
        self.record = record
        self.record_observable_proxy = ObservableProxy(record, sync=True)
        # Rebind widgets - this is called by the decorator
        self._rebind_record_widgets()

    def _rebind_record_widgets(self) -> None:
        """Rebind all auto-bound widgets to the new record. Called internally."""
        # This will be implemented by the @widget decorator processing
        pass

    # Lifecycle hooks - override these in subclasses
    def configure(self) -> None:
        """Called early, before bindings are processed. Override to configure widgets."""
        pass

    def setup(self) -> None:
        """Called after bindings are processed. Override for final setup."""
        pass

    # =========================================================================
    # Stylesheet Loading
    # =========================================================================

    def load_stylesheet(
        self,
        path: str | None = None,
        qrc_path: str | None = None,
    ) -> None:
        """
        Load a stylesheet from a file path or QRC resource.

        Args:
            path: Path to a .qss file.
            qrc_path: Optional QRC resource path for fallback.
        """
        stylesheet = _load_stylesheet(qss_path=path, qrc_path=qrc_path)
        if stylesheet:
            # Widget is a mixin used with QWidget, so self has setStyleSheet
            cast(QWidget, self).setStyleSheet(stylesheet)

    # =========================================================================
    # Validation - delegate to self.record_observable_proxy
    # =========================================================================

    def add_validator(self, field: str, validator: Callable[[Any], str | None]) -> None:
        """
        Add a validator to a record field.

        Args:
            field: The field name to validate.
            validator: Function that takes the field value and returns
                      None if valid, or an error message string if invalid.

        Example:
            self.add_validator("name", lambda v: "Required" if not v else None)
            self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)
        """
        self.record_observable_proxy.add_validator(field, validator)

    def is_valid(self) -> Any:
        """
        Get an observable indicating whether all fields are valid.

        Returns:
            IObservable that emits True when all validators pass, False otherwise.

        Example:
            self.is_valid().on_change(lambda valid: self.save_btn.setEnabled(valid))
        """
        return self.record_observable_proxy.is_valid()

    def validation_for(self, field: str) -> Any:
        """
        Get an observable list of validation errors for a specific field.

        Args:
            field: The field name.

        Returns:
            IObservable list of error messages (empty if valid).

        Example:
            self.validation_for("email").on_change(self.show_email_errors)
        """
        return self.record_observable_proxy.validation_for(field)

    def validation_errors(self) -> Any:
        """
        Get an observable dict of all validation errors.

        Returns:
            IObservableDict mapping field names to lists of error messages.

        Example:
            errors = self.validation_errors().get()
            for field, messages in errors.items():
                print(f"{field}: {', '.join(messages)}")
        """
        return self.record_observable_proxy.validation_errors()

    # =========================================================================
    # Dirty Tracking - delegate to self.record_observable_proxy
    # =========================================================================

    def is_dirty(self) -> bool:
        """
        Check whether any field has been modified.

        Returns:
            True if any field is dirty, False otherwise.

        Example:
            if self.is_dirty():
                self.status.setText("Modified")
        """
        return self.record_observable_proxy.is_dirty()

    def dirty_fields(self) -> set[str]:
        """
        Get the set of dirty field names.

        Returns:
            Set of field names that have been modified.

        Example:
            for field in self.dirty_fields():
                print(f"Modified: {field}")
        """
        return self.record_observable_proxy.dirty_fields()

    def reset_dirty(self) -> None:
        """
        Reset dirty state, making current values the new baseline.

        Example:
            self.save_to(self.record)
            self.reset_dirty()  # Mark all fields as clean
        """
        self.record_observable_proxy.reset_dirty()

    # =========================================================================
    # Undo/Redo - delegate to self.record_observable_proxy
    # =========================================================================

    def undo(self, field: str) -> None:
        """
        Undo the last change to a field.

        Args:
            field: The field name.

        Note:
            Requires @widget(undo=True) to be enabled.

        Example:
            if self.can_undo("name"):
                self.undo("name")
        """
        self.record_observable_proxy.undo(field)

    def redo(self, field: str) -> None:
        """
        Redo the last undone change to a field.

        Args:
            field: The field name.

        Note:
            Requires @widget(undo=True) to be enabled.

        Example:
            if self.can_redo("name"):
                self.redo("name")
        """
        self.record_observable_proxy.redo(field)

    def can_undo(self, field: str) -> bool:
        """
        Check whether undo is available for a field.

        Args:
            field: The field name.

        Returns:
            True if undo is available, False otherwise.

        Example:
            self.undo_btn.setEnabled(self.can_undo("name"))
        """
        return self.record_observable_proxy.can_undo(field)

    def can_redo(self, field: str) -> bool:
        """
        Check whether redo is available for a field.

        Args:
            field: The field name.

        Returns:
            True if redo is available, False otherwise.

        Example:
            self.redo_btn.setEnabled(self.can_redo("name"))
        """
        return self.record_observable_proxy.can_redo(field)

    # =========================================================================
    # Save/Load - delegate to self.record_observable_proxy
    # =========================================================================

    def save_to(self, target: T) -> None:
        """
        Save the current proxy state to a record instance.

        This copies all field values from the proxy to the target.

        Args:
            target: The record instance to save to.

        Example:
            self.save_to(self.record)  # Save back to original record
            self.save_to(new_user)     # Save to a different instance
        """
        self.record_observable_proxy.save_to(target)

    def load_dict(self, data: dict[str, Any]) -> None:
        """
        Load data from a dictionary into the proxy.

        Args:
            data: Dictionary of field names to values.

        Example:
            self.load_dict({"name": "Alice", "age": 30})
        """
        self.record_observable_proxy.load_dict(data)


def get_model_type_from_widget[T](cls: type[Widget[T]]) -> type[T] | None:
    """
    Extract the type parameter T from a Widget[T] subclass.

    Args:
        cls: A class that inherits from Widget[T]

    Returns:
        The type T, or None if not provided or can't be determined
    """
    # Walk through the class's bases to find Widget[T]
    for base in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(base)
        if origin is Widget:
            args = get_args(base)
            if args and args[0] is not type(None):
                return args[0]  # type: ignore[return-value]
    return None


def is_widget_subclass(cls: type[object]) -> bool:
    """Check if a class is a subclass of Widget."""
    try:
        return issubclass(cls, Widget)
    except TypeError:
        return False


def has_model_type_param(cls: type[object]) -> bool:
    """Check if a Widget subclass has a type parameter (e.g., Widget[Dog] vs Widget)."""
    for base in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(base)
        if origin is Widget:
            args = get_args(base)
            # Has type param if args exist and it's not None
            return bool(args) and args[0] is not type(None)
    return False


# Keep ModelWidget as an alias for backwards compatibility
ModelWidget = Widget
