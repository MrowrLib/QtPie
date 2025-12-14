"""ModelWidget base class for widgets with automatic model binding."""

from __future__ import annotations

from typing import TYPE_CHECKING, get_args, get_origin

from observant import ObservableProxy  # type: ignore[import-untyped]

# Sentinel to detect if model field used make_later()
MAKE_LATER_SENTINEL = object()


class ModelWidget[T]:
    """
    Base class for widgets with automatic model binding.

    ModelWidget provides:
    - Automatic model creation (T() by default)
    - Automatic proxy creation (ObservableProxy wrapping the model)
    - Auto-binding of widget fields to model properties by matching names

    Usage:
        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        # Auto-creates Person() as model
        @widget()
        class PersonEditor(ModelWidget[Person]):
            name: QLineEdit = make(QLineEdit)  # auto-binds to model.name
            age: QSpinBox = make(QSpinBox)      # auto-binds to model.age

        # Custom model initialization
        @widget()
        class PersonEditor(ModelWidget[Person]):
            model: Person = make(Person, name="Unknown", age=0)
            name: QLineEdit = make(QLineEdit)

        # Manual model setup
        @widget()
        class PersonEditor(ModelWidget[Person]):
            model: Person = make_later()
            name: QLineEdit = make(QLineEdit)

            def setup(self) -> None:
                self.model = load_person_from_db()
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


def get_model_type[T](cls: type[ModelWidget[T]]) -> type[T] | None:
    """
    Extract the type parameter T from a ModelWidget[T] subclass.

    Args:
        cls: A class that inherits from ModelWidget[T]

    Returns:
        The type T, or None if it can't be determined
    """
    # Walk through the class's bases to find ModelWidget[T]
    for base in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(base)
        if origin is ModelWidget:
            args = get_args(base)
            if args:
                return args[0]  # type: ignore[return-value]
    return None


def is_model_widget_subclass(cls: type[object]) -> bool:
    """Check if a class is a subclass of ModelWidget."""
    try:
        return issubclass(cls, ModelWidget)
    except TypeError:
        return False
