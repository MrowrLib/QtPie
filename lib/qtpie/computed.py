"""Computed[T] - read-only derived variables."""

import re
from typing import Any, NoReturn, cast, overload, override

from observant import Observable

from .variable import Variable


class Computed[T](Variable[T, None]):
    """A read-only Variable whose value is derived from an expression.

    Usage:
        _doubled: Computed[int] = new("{_count * 2}")

    The value is automatically recomputed when any referenced Variable changes.
    Attempting to set the value raises AttributeError.
    """

    @Variable.value.setter
    def value(self, val: T) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot set Computed value - it's derived from an expression")

    # Block augmented assignment operators
    @override
    def __iadd__(self, other: Any) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot modify Computed value")

    @override
    def __isub__(self, other: Any) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot modify Computed value")

    @override
    def __imul__(self, other: Any) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot modify Computed value")

    @override
    def __itruediv__(self, other: Any) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot modify Computed value")

    @override
    def __ifloordiv__(self, other: Any) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot modify Computed value")

    @override
    def __imod__(self, other: Any) -> NoReturn:  # pyright: ignore[reportReturnType] - raises
        raise AttributeError("Cannot modify Computed value")


# Regex to find variable references in expressions like "{_count * 2}" or "{_first} {_last}"
_VAR_PATTERN = re.compile(r"\{([^}]+)\}")
_IDENTIFIER_PATTERN = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")


def _extract_var_names(expression: str) -> list[str]:
    """Extract potential variable names from an expression.

    Args:
        expression: Expression like "{_count * 2}" or "{_first} {_last}"

    Returns:
        List of potential variable names found in the expression.
    """
    var_names: list[str] = []

    # Find all {expression} blocks
    for match in _VAR_PATTERN.finditer(expression):
        expr_content = match.group(1)
        # Find all identifiers in the expression
        for ident_match in _IDENTIFIER_PATTERN.finditer(expr_content):
            ident = ident_match.group()
            # Skip Python builtins and keywords
            if ident not in {"len", "str", "int", "float", "bool", "list", "dict", "set", "True", "False", "None", "if", "else", "and", "or", "not", "in"}:
                if ident not in var_names:
                    var_names.append(ident)

    return var_names


class _ComputedDescriptor:
    """Descriptor that creates per-instance Computed objects.

    Handles expression evaluation and reactive subscriptions.
    """

    def __init__(self, name: str, expression: str, inner_type: type | None = None) -> None:
        self._name = name
        self._expression = expression
        self._inner_type = inner_type
        # Cache for per-instance Computed objects
        self._instance_cache: dict[int, Computed[Any]] = {}

    @overload
    def __get__(self, obj: None, objtype: type) -> Computed[Any]: ...

    @overload
    def __get__(self, obj: object, objtype: type) -> Computed[Any]: ...

    def __get__(self, obj: object | None, objtype: type) -> Computed[Any]:
        if obj is None:
            # Class-level access - return a placeholder
            return cast(Computed[Any], self)

        # Check if we already created this Computed for this instance
        obj_id = id(obj)
        if obj_id in self._instance_cache:
            return self._instance_cache[obj_id]

        # Create the Computed for this instance
        computed = self._create_computed(obj)
        self._instance_cache[obj_id] = computed
        return computed

    def __set__(self, obj: object, value: Any) -> None:
        raise AttributeError("Cannot set Computed value - it's derived from an expression")

    def _create_computed(self, context: Any) -> Computed[Any]:
        """Create a Computed instance and set up reactive bindings.

        Args:
            context: The widget instance providing the variable context.

        Returns:
            A Computed that updates when dependencies change.
        """
        # Find all Variables this expression depends on
        var_names = _extract_var_names(self._expression)
        # Capture our own name to avoid self-reference in compute()
        own_name = self._name
        observables: list[Observable[Any]] = []
        observable_proxies: list[Any] = []

        for var_name in var_names:
            # Build list of names to try
            # If name already starts with underscore, don't add another
            if var_name.startswith("_"):
                names_to_try = [var_name]
            else:
                names_to_try = [f"_{var_name}", var_name]

            for attr_name in names_to_try:
                # Use object's __dict__ to avoid triggering the descriptor we're creating
                if attr_name in type(context).__dict__:
                    descriptor = type(context).__dict__[attr_name]
                    # Skip if this is the descriptor we're currently creating
                    if descriptor is self:
                        continue
                    # Check if it's a Variable or Computed descriptor
                    is_variable_desc = hasattr(descriptor, "_default")  # _VariableDescriptor
                    is_computed_desc = isinstance(descriptor, _ComputedDescriptor)
                    if is_variable_desc or is_computed_desc:
                        attr = getattr(context, attr_name)
                        if isinstance(attr, Variable):
                            wrapper = attr.observable  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                            if isinstance(wrapper, Observable):
                                observables.append(wrapper)  # pyright: ignore[reportUnknownArgumentType]
                            else:
                                # ObservableList, ObservableDict, ObservableProxy
                                observable_proxies.append(wrapper)
                            break

        # Also check record fields if Widget[T]
        if hasattr(context, "_qtpie_config"):
            config = context._qtpie_config
            if hasattr(config, "record_type") and config.record_type is not None:
                if hasattr(context, "record") and hasattr(context.record, "observable"):
                    record_proxy = context.record.observable
                    if record_proxy not in observable_proxies:
                        observable_proxies.append(record_proxy)

        def compute() -> Any:
            """Evaluate the expression with current variable values."""
            # Build context dict
            eval_context: dict[str, Any] = {}

            for var_name in var_names:
                # Build list of names to try
                if var_name.startswith("_"):
                    names_to_try = [var_name]
                else:
                    names_to_try = [f"_{var_name}", var_name]

                for attr_name in names_to_try:
                    # Skip our own name to avoid self-reference
                    if attr_name == own_name:
                        continue
                    # Use object's __dict__ to check descriptor type
                    if attr_name in type(context).__dict__:
                        descriptor = type(context).__dict__[attr_name]
                        is_variable_desc = hasattr(descriptor, "_default")
                        is_computed_desc = isinstance(descriptor, _ComputedDescriptor)
                        if is_variable_desc or is_computed_desc:
                            attr = getattr(context, attr_name)
                            if isinstance(attr, Variable):
                                eval_context[var_name] = attr.value  # pyright: ignore[reportUnknownMemberType]
                            else:
                                eval_context[var_name] = attr
                            break

            # Also add record fields if Widget[T]
            if hasattr(context, "_qtpie_config"):
                config = context._qtpie_config
                if hasattr(config, "record_type") and config.record_type is not None:
                    if hasattr(context, "record"):
                        record = context.record
                        # Add record fields to context
                        if hasattr(record, "value") and record.value is not None:
                            for field_name in var_names:
                                if field_name not in eval_context and hasattr(record.value, field_name):
                                    eval_context[field_name] = getattr(record.value, field_name)

            # Evaluate the expression
            # Handle both "{expr}" format and plain expressions
            expr = self._expression
            if expr.startswith("{") and expr.endswith("}") and expr.count("{") == 1:
                # Simple single expression: "{_count * 2}"
                expr = expr[1:-1]
                try:
                    return eval(expr, {"__builtins__": __builtins__}, eval_context)  # noqa: S307
                except Exception:
                    return None
            else:
                # Format string: "{_first} {_last}"
                result = self._expression
                for match in _VAR_PATTERN.finditer(self._expression):
                    expr_content = match.group(1)
                    full_match = match.group(0)
                    try:
                        value = eval(expr_content, {"__builtins__": __builtins__}, eval_context)  # noqa: S307
                        result = result.replace(full_match, str(value))
                    except Exception:
                        result = result.replace(full_match, "")
                return result

        # Create Observable with initial computed value
        initial_value = compute()
        observable: Observable[Any] = Observable(initial_value)

        # Create the Computed with this observable
        computed: Computed[Any] = Computed(observable)

        # Subscribe to all dependencies to recompute when they change
        def on_change(_: Any = None) -> None:
            new_value = compute()
            observable.set(new_value)

        for obs in observables:
            obs.on_change(on_change)

        for proxy in observable_proxies:
            if hasattr(proxy, "on_change"):
                proxy.on_change(lambda: on_change())

        return computed


def create_computed_descriptor(
    name: str,
    expression: str,
    inner_type: type | None = None,
) -> _ComputedDescriptor:
    """Create a computed descriptor. Used by NewField."""
    return _ComputedDescriptor(name, expression, inner_type)
