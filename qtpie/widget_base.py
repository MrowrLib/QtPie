"""Widget base class - optional mixin with model binding support."""

from typing import TYPE_CHECKING, get_args, get_origin

from observant import ObservableProxy
from qtpy.QtWidgets import QLayout


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
    if TYPE_CHECKING:
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
