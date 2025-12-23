"""Widget base class - optional mixin with model binding support."""

from collections.abc import Callable
from typing import Any, cast, get_args, get_origin

from observant import ObservableProxy
from qtpy.QtWidgets import QLayout, QWidget

from qtpie.styles.loader import load_stylesheet as _load_stylesheet


class Widget[T = None]:
    """
    Base class for widgets with optional model binding.

    Widget can be used in two ways:

    1. **Without type parameter** - Just a mixin, no model binding:
       ```python
       @widget()
       class SimpleWidget(QWidget, Widget):
           label: QLabel = make(QLabel, "Hello")
       ```

    2. **With type parameter** - Enables automatic model binding:
       ```python
       @widget()
       class DogEditor(QWidget, Widget[Dog]):
           name: QLineEdit = make(QLineEdit)  # auto-binds to model.name
           age: QSpinBox = make(QSpinBox)      # auto-binds to model.age
       ```

    When a type parameter is provided:
    - Model is auto-created as `T()` by default
    - Custom model via `model: Dog = make(Dog, name="Buddy")`
    - Manual setup via `model: Dog = make_later()` + set in `setup()`
    - `ObservableProxy` is auto-created wrapping the model
    - Widget fields auto-bind to model properties by matching names
    """

    # Type hints for IDE - actual fields are created by @widget decorator
    model: T
    proxy: ObservableProxy[T]

    def set_model(self, model: T) -> None:
        """
        Set a new model and rebind all widgets.

        This allows changing the model after widget creation.
        """
        self.model = model
        self.proxy = ObservableProxy(model, sync=True)
        # Rebind widgets - this is called by the decorator
        self._rebind_model_widgets()

    def _rebind_model_widgets(self) -> None:
        """Rebind all auto-bound widgets to the new model. Called internally."""
        # This will be implemented by the @widget decorator processing
        pass

    # Lifecycle hooks - override these in subclasses
    def setup(self) -> None:
        """Called after widget initialization. Override to set up initial state."""
        pass

    def setup_values(self) -> None:
        """Called after setup(). Override to initialize values."""
        pass

    def setup_bindings(self) -> None:
        """Called after setup_values(). Override to set up data bindings."""
        pass

    def setup_layout(self, layout: QLayout) -> None:
        """Called after setup_bindings() if widget has a layout. Override to customize layout."""
        pass

    def setup_styles(self) -> None:
        """Called after setup_layout(). Override to apply styles."""
        pass

    def setup_events(self) -> None:
        """Called after setup_styles(). Override to set up event handlers."""
        pass

    def setup_signals(self) -> None:
        """Called after setup_events(). Override to connect signals."""
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
    # Validation - delegate to self.proxy
    # =========================================================================

    def add_validator(self, field: str, validator: Callable[[Any], str | None]) -> None:
        """
        Add a validator to a model field.

        Args:
            field: The field name to validate.
            validator: Function that takes the field value and returns
                      None if valid, or an error message string if invalid.

        Example:
            self.add_validator("name", lambda v: "Required" if not v else None)
            self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)
        """
        self.proxy.add_validator(field, validator)

    def is_valid(self) -> Any:
        """
        Get an observable indicating whether all fields are valid.

        Returns:
            IObservable that emits True when all validators pass, False otherwise.

        Example:
            self.is_valid().on_change(lambda valid: self.save_btn.setEnabled(valid))
        """
        return self.proxy.is_valid()

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
        return self.proxy.validation_for(field)

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
        return self.proxy.validation_errors()

    # =========================================================================
    # Dirty Tracking - delegate to self.proxy
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
        return self.proxy.is_dirty()

    def dirty_fields(self) -> set[str]:
        """
        Get the set of dirty field names.

        Returns:
            Set of field names that have been modified.

        Example:
            for field in self.dirty_fields():
                print(f"Modified: {field}")
        """
        return self.proxy.dirty_fields()

    def reset_dirty(self) -> None:
        """
        Reset dirty state, making current values the new baseline.

        Example:
            self.save_to(self.model)
            self.reset_dirty()  # Mark all fields as clean
        """
        self.proxy.reset_dirty()

    # =========================================================================
    # Undo/Redo - delegate to self.proxy
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
        self.proxy.undo(field)

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
        self.proxy.redo(field)

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
        return self.proxy.can_undo(field)

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
        return self.proxy.can_redo(field)

    # =========================================================================
    # Save/Load - delegate to self.proxy
    # =========================================================================

    def save_to(self, target: T) -> None:
        """
        Save the current proxy state to a model instance.

        This copies all field values from the proxy to the target.

        Args:
            target: The model instance to save to.

        Example:
            self.save_to(self.model)  # Save back to original model
            self.save_to(new_user)    # Save to a different instance
        """
        self.proxy.save_to(target)

    def load_dict(self, data: dict[str, Any]) -> None:
        """
        Load data from a dictionary into the proxy.

        Args:
            data: Dictionary of field names to values.

        Example:
            self.load_dict({"name": "Alice", "age": 30})
        """
        self.proxy.load_dict(data)


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
