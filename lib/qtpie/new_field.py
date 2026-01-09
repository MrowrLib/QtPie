"""NewField - Stores field configuration for deferred instantiation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, get_args, get_origin, get_type_hints

from .layout import GridPosition
from .variable import Variable, create_variable_descriptor


class NewField:
    """Stores args/kwargs for deferred field instantiation.

    For Variable[T] annotations: replaces itself with a Variable descriptor.
    For list[QWidget] annotations: stores binding info for list widget creation.
    For QWidget types: tracks layout inclusion/exclusion.
    For other types: @new_fields handles instantiation, passing all args/kwargs.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs
        self.name: str = ""
        self.field_type: type | None = None
        self.exclude_from_layout = False
        self.bind: str | Any | None = None  # Extracted for QWidgets in __set_name__ (can be Translatable)
        self.signal_connections: dict[str, str | Callable[..., Any]] = {}  # signal_name -> method_name or callable
        self.widget_props: dict[str, Any] = {}  # propName -> value (becomes setPropName(value))
        # Layout params for form/grid layouts
        self.label: str | None = None  # For form layouts: new(label="Name")
        self.grid: GridPosition | None = None  # For grid layouts: new(grid=(0, 0)) or (row, col, rowspan, colspan)
        # Widget args for Variable[T, W] - set via __call__
        self.widget_args: tuple[Any, ...] = ()
        self.widget_kwargs: dict[str, Any] = {}
        # list[QWidget] support
        self.is_list_widget: bool = False
        self.list_widget_type: type | None = None  # The QWidget type inside list[QWidget]
        self.list_format: str | Callable[[Any], str] | None = None  # Format for list items
        # Object name and CSS classes
        self.object_name: str | None = None  # objectName for the widget
        self.css_classes: list[str] = []  # CSS classes for the widget
        # Property bindings (visible="_is_visible", enabled="{_count > 0}")
        self.property_bindings: dict[str, str] = {}  # prop_name -> binding expression
        # Translation support - track Translatable markers for binding registration
        self.translatable_args: list[tuple[int, Any]] = []  # (index, Translatable)
        self.translatable_kwargs: dict[str, Any] = {}  # kwarg_name -> Translatable
        # Variable bindings - maps child's required Variable names to parent's values/expressions
        self.variable_bindings: dict[str, Any] = {}  # child_var_name -> binding_value
        # Ref bindings - deferred attribute references to resolve after field instantiation
        self.ref_bindings: dict[str, Any] = {}  # kwarg_name -> Ref instance

    def __call__(self, *widget_args: Any, **widget_kwargs: Any) -> NewField:
        """Store widget constructor args: new("value")(placeholder="...").

        For Variable[T, W], the first new() call stores Variable args,
        and the second call stores widget constructor args.
        """
        self.widget_args = widget_args
        self.widget_kwargs = widget_kwargs
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

        # Normalize aliases (title -> windowTitle, stylesheet -> styleSheet)
        self._normalize_kwargs_aliases()

        # Get the type annotation
        hints = get_type_hints(owner)
        self.field_type = hints.get(name)

        # If it's a Variable, replace self with a Variable descriptor
        origin = get_origin(self.field_type)
        if origin is Variable or self.field_type is Variable:
            default = self._get_variable_default()
            # Extract inner type from Variable[T] and optional widget type from Variable[T, W]
            inner_type: type | None = None
            widget_type: type | None = None
            if origin is Variable:
                args = get_args(self.field_type)
                inner_type = args[0] if args else None
                widget_type = args[1] if len(args) > 1 else None

            # Extract layout params from widget_kwargs (they're layout params, not widget constructor params)
            widget_kwargs_copy = dict(self.widget_kwargs)
            label = widget_kwargs_copy.pop("label", None)
            grid = widget_kwargs_copy.pop("grid", None)
            layout_kwarg = widget_kwargs_copy.pop("layout", None)
            exclude_from_layout = layout_kwarg is False

            # Extract name= and classes= for widget configuration (not constructor params)
            object_name: str | None = widget_kwargs_copy.pop("name", None)
            css_classes: list[str] = widget_kwargs_copy.pop("classes", None) or []

            # Extract validate= for auto-registering validators (only in kwargs, not widget_kwargs)
            validators = self.kwargs.pop("validate", None)

            descriptor = create_variable_descriptor(
                default,
                name,
                inner_type,
                widget_type,
                self.widget_args,
                widget_kwargs_copy,
                label,
                grid,
                exclude_from_layout,
                validators,
                object_name,
                css_classes,
            )
            setattr(owner, name, descriptor)
            return

        # Handle list[QWidget] - creates a WidgetRepeater bound to a list source
        if origin is list:
            type_args = get_args(self.field_type)
            if type_args and self._is_qwidget_class(type_args[0]):
                self.is_list_widget = True
                self.list_widget_type = type_args[0]

                # Extract bind= (required for list widgets)
                self.bind = self.kwargs.pop("bind", None)

                # Extract format= for list item formatting (string template or callable)
                self.list_format = self.kwargs.pop("format", None)

                # layout=False → exclude from layout
                layout_kwarg = self.kwargs.pop("layout", None)
                if layout_kwarg is False:
                    self.exclude_from_layout = True

                # Extract label= for form layouts
                self.label = self.kwargs.pop("label", None)

                # Extract grid= for grid layouts
                self.grid = self.kwargs.pop("grid", None)

                # Extract name= for objectName (applied to each widget in list)
                self.object_name = self.kwargs.pop("name", None)

                # Extract classes= for CSS classes (applied to each widget in list)
                classes = self.kwargs.pop("classes", None)
                if classes is not None:
                    self.css_classes = classes

                # Extract widget props (e.g., styleSheet="..." → setStyleSheet)
                # Use list_widget_type for setter detection
                self._extract_widget_props(self.list_widget_type)

                # Extract Translatable markers for binding registration
                self._extract_translatables()

                # Remaining kwargs go to widget constructor
                return

            # Handle list[QAction] - creates an ActionRepeater in @menu
            if type_args and self._is_qaction_class(type_args[0]):
                # Mark as action list (not widget list, but similar handling)
                self.is_list_widget = False  # Not a widget list

                # Extract bind= (required for action lists)
                self.bind = self.kwargs.pop("bind", None)

                # Extract format= for list item formatting
                self.list_format = self.kwargs.pop("format", None)

                # Extract signal connections (e.g., triggered="on_select")
                self._extract_signal_connections_for_type(type_args[0])

                return

        # Handle QWidget-specific kwargs only
        # For non-QWidgets: leave bind= and layout= in kwargs so they pass to constructor
        if self._is_qwidget_type():
            # Extract refs FIRST (before other extractions might modify kwargs)
            self._extract_refs()

            # Extract bind= for QtPie binding system
            self.bind = self.kwargs.pop("bind", None)

            # layout=False → exclude from layout
            layout_kwarg = self.kwargs.pop("layout", None)
            if layout_kwarg is False:
                self.exclude_from_layout = True

            # Extract label= for form layouts
            self.label = self.kwargs.pop("label", None)

            # Extract grid= for grid layouts
            self.grid = self.kwargs.pop("grid", None)

            # Extract variable bindings for QtPie Widget subclasses BEFORE extracting name=
            # This ensures that if a child widget has a required Variable called "name",
            # it gets treated as a variable binding, not as objectName
            # e.g., child: Child = new(count="_my_count", name="_my_name")
            self._extract_variable_bindings()

            # Extract name= for objectName (only if it wasn't already extracted as a variable binding)
            if "name" not in self.variable_bindings:
                self.object_name = self.kwargs.pop("name", None)

            # Extract classes= for CSS classes
            classes = self.kwargs.pop("classes", None)
            if classes is not None:
                self.css_classes = classes

            # Extract signal connections (e.g., clicked="on_clicked")
            self._extract_signal_connections()

            # Extract widget props (e.g., windowTitle="Foo" → setWindowTitle("Foo"))
            self._extract_widget_props()

            # Extract Translatable markers for binding registration
            self._extract_translatables()

        # Handle QObject subclasses (not QWidget, but have signals and props)
        # This covers QAction, QMenu, etc.
        elif self._is_qobject_type():
            # Extract refs FIRST (before other extractions might modify kwargs)
            self._extract_refs()

            # Extract signal connections (e.g., triggered="on_triggered")
            self._extract_signal_connections()

            # Extract widget props (e.g., shortcut="Ctrl+N" → setShortcut)
            self._extract_widget_props()

            # Extract Translatable markers for binding registration
            self._extract_translatables()

    def _normalize_kwargs_aliases(self) -> None:
        """Normalize convenience aliases in kwargs.

        Converts:
            title -> windowTitle
            stylesheet -> styleSheet
            tooltip -> toolTip
        """
        if "title" in self.kwargs:
            self.kwargs["windowTitle"] = self.kwargs.pop("title")
        if "stylesheet" in self.kwargs:
            self.kwargs["styleSheet"] = self.kwargs.pop("stylesheet")
        if "tooltip" in self.kwargs:
            self.kwargs["toolTip"] = self.kwargs.pop("tooltip")

    def _is_qwidget_type(self) -> bool:
        """Check if the field type is a QWidget subclass."""
        return self._is_qwidget_class(self.field_type)

    def _is_qobject_type(self) -> bool:
        """Check if the field type is a QObject subclass (but not QWidget)."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtCore import QObject
            from qtpy.QtWidgets import QWidget

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            # Is a QObject but NOT a QWidget (QWidget handled separately above)
            return issubclass(self.field_type, QObject) and not issubclass(self.field_type, QWidget)
        except (ImportError, TypeError):
            return False

    def _is_qwidget_class(self, cls: type | None) -> bool:
        """Check if cls is a QWidget subclass."""
        if cls is None:
            return False
        try:
            from qtpy.QtWidgets import QWidget

            # cls could be a generic alias, so check it's a proper type
            return isinstance(cls, type) and issubclass(cls, QWidget)  # pyright: ignore[reportUnnecessaryIsInstance]
        except (ImportError, TypeError):
            return False

    def _is_qaction_class(self, cls: type | None) -> bool:
        """Check if cls is QAction."""
        if cls is None:
            return False
        try:
            from qtpy.QtGui import QAction

            return cls is QAction or (isinstance(cls, type) and issubclass(cls, QAction))  # pyright: ignore[reportUnnecessaryIsInstance]
        except (ImportError, TypeError):
            return False

    def _is_signal(self, name: str) -> bool:
        """Check if name is a signal on the field type."""
        if self.field_type is None:
            return False
        try:
            attr = getattr(self.field_type, name, None)
            if attr is None:
                return False
            # qtpy signals at class level have type name 'Signal'
            return type(attr).__name__ == "Signal"
        except Exception:
            return False

    def _extract_signal_connections(self) -> None:
        """Extract signal=handler kwargs for QWidgets.

        Supports both callables and string method names:
            clicked=lambda: print("clicked")
            clicked="on_clicked"
        """
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg name matches a signal on the widget type
            if self._is_signal(key):
                # Value must be a string (method name) or callable
                if isinstance(value, str) or callable(value):
                    self.signal_connections[key] = value
                    to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _extract_signal_connections_for_type(self, target_type: type) -> None:
        """Extract signal=handler kwargs for a specific type (e.g., QAction for list[QAction]).

        Args:
            target_type: The type to check for signals (e.g., QAction)
        """
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg name matches a signal on the target type
            if self._is_signal_on_type(key, target_type):
                # Value must be a string (method name) or callable
                if isinstance(value, str) or callable(value):
                    self.signal_connections[key] = value
                    to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _is_signal_on_type(self, name: str, target_type: type) -> bool:
        """Check if name is a signal on the given type."""
        try:
            attr = getattr(target_type, name, None)
            if attr is None:
                return False
            # qtpy signals at class level have type name 'Signal'
            return type(attr).__name__ == "Signal"
        except Exception:
            return False

    def _has_setter(self, prop_name: str, widget_type: type | None = None) -> bool:
        """Check if the widget type has a setXxx method for the given property name."""
        check_type = widget_type or self.field_type
        if check_type is None:
            return False
        try:
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            attr = getattr(check_type, setter_name, None)
            return attr is not None and callable(attr)
        except Exception:
            return False

    def _is_binding_expression(self, value: Any) -> bool:
        """Check if value is a binding expression (string reference or {expr})."""
        if not isinstance(value, str):
            return False
        # If it contains {}, it's definitely a binding expression
        if "{" in value and "}" in value:
            return True
        # If it's a simple identifier (possibly with underscore prefix), treat as variable reference
        # But NOT if it looks like a regular value (e.g., "true", "false", urls, paths, etc.)
        stripped = value.strip()
        if not stripped:
            return False
        # Check if it's a valid Python identifier (variable/method name)
        # This catches things like "_is_visible", "should_show", but not "hello world"
        return stripped.replace("_", "").replace(".", "").isalnum() and stripped[0].isalpha() or stripped[0] == "_"

    def _extract_widget_props(self, widget_type: type | None = None) -> None:
        """Extract property kwargs for QWidgets.

        For kwargs like windowTitle="Foo", if the widget class has a
        setWindowTitle method, extract it to widget_props for later application.

        If the value is a string that looks like a binding expression (e.g., "_is_visible"
        or "{_count > 0}"), it's stored in property_bindings instead.

        Args:
            widget_type: The widget type to check for setters. If None, uses self.field_type.
        """
        # Properties that support binding (common QWidget/QAction properties)
        bindable_props = {"visible", "enabled", "windowModified", "acceptDrops", "updatesEnabled", "checked"}

        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg corresponds to a setter on the widget type
            if self._has_setter(key, widget_type):
                # Check if this is a bindable property with a binding expression
                if key in bindable_props and self._is_binding_expression(value):
                    self.property_bindings[key] = value
                else:
                    self.widget_props[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _extract_translatables(self) -> None:
        """Extract Translatable markers from args and widget_props for binding registration.

        Translatables are kept in place (not resolved here) - they're resolved
        during widget instantiation in new_fields.py.
        """
        from qtpie.translations.translatable import Translatable

        # Check positional args for Translatable markers
        for i, arg in enumerate(self.args):
            if isinstance(arg, Translatable):
                self.translatable_args.append((i, arg))

        # Check widget_props for Translatable markers
        for key, value in self.widget_props.items():
            if isinstance(value, Translatable):
                self.translatable_kwargs[key] = value

        # Also check remaining kwargs (for widgets that take text in constructor)
        for key, value in self.kwargs.items():
            if isinstance(value, Translatable):
                self.translatable_kwargs[key] = value

    def _extract_variable_bindings(self) -> None:
        """Extract variable bindings for QtPie Widget subclasses.

        When the field type is a QtPie Widget with required/optional Variable bindings,
        extract matching kwargs as variable_bindings instead of passing to constructor.

        Example:
            child: Child = new(count="_my_count")  # count is extracted as a binding
        """
        if self.field_type is None:
            return

        # Check if the field type is a QtPie Widget subclass
        if not self._is_qtpie_widget():
            return

        # Get the child's required bindings and all Variable annotations
        config = getattr(self.field_type, "_qtpie_config", None)
        if config is None:
            return

        # Collect all Variable names from the child (required and optional)
        variable_names: set[str] = set(config.required_bindings)

        # Also check annotations for Variable types (including optional ones with defaults)
        child_annotations = getattr(self.field_type, "__annotations__", {})
        for name, annotation in child_annotations.items():
            origin = get_origin(annotation)
            if origin is Variable or annotation is Variable:
                variable_names.add(name)

        # Extract kwargs that match Variable names
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            if key in variable_names:
                self.variable_bindings[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _is_qtpie_widget(self) -> bool:
        """Check if the field type is a QtPie Widget subclass (has _qtpie_config)."""
        if self.field_type is None:
            return False
        return hasattr(self.field_type, "_qtpie_config")

    def _get_variable_default(self) -> Any:
        """Extract default value for a Variable field."""
        # Check for explicit default= kwarg
        if "default" in self.kwargs:
            return self.kwargs["default"]
        # Check for single arg (primitive, list, dict, or object)
        if len(self.args) == 1:
            return self.args[0]
        return None

    def _extract_refs(self) -> None:
        """Extract Ref markers from kwargs for deferred resolution.

        Ref instances are removed from kwargs and stored in ref_bindings.
        They will be resolved after field instantiation when sibling fields exist.
        """
        from .ref import Ref

        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            if isinstance(value, Ref):
                self.ref_bindings[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]
