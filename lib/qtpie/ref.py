"""ref - Deferred attribute references for declarative field definitions."""

import ast
from typing import Any, override

# Python builtins that shouldn't be treated as widget attributes (for expressions)
_BUILTINS = frozenset(
    {
        "len",
        "str",
        "int",
        "float",
        "bool",
        "abs",
        "min",
        "max",
        "sum",
        "round",
        "sorted",
        "list",
        "dict",
        "set",
        "tuple",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "any",
        "all",
        "True",
        "False",
        "None",
        "repr",
        "type",
        "isinstance",
        "hasattr",
        "getattr",
        "ord",
        "chr",
        "hex",
        "bin",
        "oct",
    }
)


def _extract_ast_names(expr: str) -> set[str]:
    """Extract all variable names from a Python expression using AST.

    Only returns top-level names (for 'dog.name', returns 'dog').
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _is_expression_ref(name: str) -> bool:
    """Check if the ref contains expression placeholders {}.

    Returns True for:
        - "{_attr}"
        - "Count: {len(_items)}"
        - "Name: {_name}, Age: {_age}"

    Returns False for:
        - "_attr"
        - "#parent._attr"
        - "_attr.nested.path"
    """
    return "{" in name and "}" in name


class Ref:
    """Marker for deferred attribute reference.

    Used in new() to reference sibling fields that haven't been created yet
    at class definition time. Resolved after all fields are instantiated.

    Examples:
        # Reference a sibling field
        _menu: TrayMenu = new()
        _tray: QSystemTrayIcon = new(contextMenu=ref("_menu"))

        # Reference a nested attribute
        _editor: TextEditor = new()
        _font_btn: QPushButton = new(font=ref("_editor.document.defaultFont"))

        # Optional chaining with ?. (returns None if any part is None/missing)
        _label: QLabel = new(text=ref("_config?.theme?.name"))

        # Reference a field on the parent widget
        _tray: QSystemTrayIcon = new(contextMenu=ref("#parent._menu"))

        # Expression support - returns a string
        _label: QLabel = new(text=ref("{_name}"))  # Stringified value
        _label: QLabel = new(text=ref("Count: {len(_items)}"))  # Full expressions

    If any attribute in the chain is a Variable, resolves to .value (the underlying data).
    For expression refs (containing {}), the result is always a string.
    """

    __slots__ = ("_name",)

    def __init__(self, name: str) -> None:
        """Create a deferred reference to an attribute.

        Args:
            name: The attribute name to reference. Supports:
                  - "attr" - simple attribute
                  - "attr.nested.path" - nested attribute chain
                  - "attr?.optional.chain" - returns None if attr is None/missing
                  - "#parent.attr" - attribute on the parent widget
                  - "#parent.attr?.nested" - nested with optional chaining
                  - "{attr}" - expression, returns string
                  - "Count: {len(items)}" - full expression language
        """
        self._name = name

    @property
    def name(self) -> str:
        """The attribute name this ref points to."""
        return self._name

    @property
    def is_expression(self) -> bool:
        """Whether this is an expression ref (contains {})."""
        return _is_expression_ref(self._name)

    @property
    def is_parent_ref(self) -> bool:
        """Whether this is a reference to a parent widget attribute."""
        return self._name.startswith("#parent.")

    @property
    def target_name(self) -> str:
        """The attribute path (without #parent. prefix if present)."""
        if self.is_parent_ref:
            return self._name[8:]  # len("#parent.") == 8
        return self._name

    def resolve(self, instance: Any, parent: Any | None = None) -> Any:
        """Resolve the reference to the actual value.

        Args:
            instance: The widget instance containing the field with this ref
            parent: The parent widget instance (for #parent references)

        Returns:
            The resolved attribute value. If any attribute in the chain is a
            Variable, it's unwrapped to .value before continuing.
            Returns None if optional chaining (?.) encounters None or missing attr.
            For expression refs (containing {}), returns a formatted string.

        Raises:
            AttributeError: If a non-optional attribute in the chain doesn't exist
            ValueError: If #parent reference used but no parent provided
        """
        # Handle expression refs differently - use format binding evaluation
        if self.is_expression:
            return self._resolve_expression(instance, parent)

        return self._resolve_path(instance, parent)

    def _resolve_expression(self, instance: Any, parent: Any | None = None) -> str:
        """Resolve an expression ref like "{_name}" or "Count: {len(_items)}".

        Uses QtPie's format binding expression evaluation. Returns a string.
        """
        # Import only the template parser from format_binding (it's a more complex function)
        # We use our local _BUILTINS and _extract_ast_names to avoid private import warnings
        from .bindings.format_binding import (
            _parse_format_template,  # pyright: ignore[reportPrivateUsage]
        )
        from .variable import Variable

        template = self._name

        # Build context with attribute values from instance (and parent if needed)
        context: dict[str, Any] = {}

        # Determine base object for lookups
        # For #parent refs, the base is the parent
        # Otherwise, it's the instance
        base_obj = parent if self.is_parent_ref else instance

        # Parse template to find all variable names
        parsed = _parse_format_template(template)

        # Collect all names from expressions
        all_names: set[str] = set()
        for _literal, field in parsed:
            if field is not None:
                expr = field.expression
                # Handle special placeholders
                if expr.startswith("#"):
                    continue
                # Use AST to extract names from expression (using local function)
                names = _extract_ast_names(expr)
                all_names.update(names - _BUILTINS)

        # Build context from names
        for name in all_names:
            root_name = name.split(".")[0]
            if root_name in context:
                continue

            # Look up on base object
            if hasattr(base_obj, root_name):
                raw_attr: Any = getattr(base_obj, root_name)
                if isinstance(raw_attr, Variable):
                    context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                else:
                    context[root_name] = raw_attr
            # Try underscore prefix
            elif hasattr(base_obj, f"_{root_name}"):
                raw_attr = getattr(base_obj, f"_{root_name}")
                if isinstance(raw_attr, Variable):
                    context[root_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                else:
                    context[root_name] = raw_attr

        # Add special placeholders
        context["self"] = instance
        context["parent"] = parent

        # Process each field and build the result
        result_parts: list[str] = []

        for literal_text, field in parsed:
            result_parts.append(literal_text)

            if field is not None:
                # Handle special # placeholders
                eval_expr = field.expression
                eval_expr = eval_expr.replace("#self", "self")
                eval_expr = eval_expr.replace("#parent", "parent")

                # Evaluate the expression
                try:
                    value = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                    # If value is callable (method without parens), call it
                    if callable(value) and not isinstance(value, type):
                        value = value()
                except Exception:
                    value = f"<error: {field.expression}>"

                # Apply format spec if present
                if field.format_spec:
                    try:
                        value = format(value, field.format_spec)
                    except Exception:
                        value = str(value)
                else:
                    value = str(value)

                result_parts.append(value)

        return "".join(result_parts)

    def _resolve_path(self, instance: Any, parent: Any | None = None) -> Any:
        """Resolve a simple path ref like "_menu" or "_editor.document.font"."""
        from .variable import Variable

        # Determine which object to start from
        if self.is_parent_ref:
            if parent is None:
                raise ValueError(f"Cannot resolve '{self._name}': no parent widget available. #parent references only work for child widgets.")
            current_obj: Any = parent
        else:
            current_obj = instance

        # Split the path and traverse, handling ?. optional chaining
        attr_path = self.target_name

        # Parse path into segments: (attr_name, is_optional)
        # "foo?.bar.baz" -> [("foo", True), ("bar", False), ("baz", False)]
        segments: list[tuple[str, bool]] = []
        remaining = attr_path
        while remaining:
            # Check for ?. (optional) or . (required)
            optional_idx = remaining.find("?.")
            regular_idx = remaining.find(".")

            if optional_idx == -1 and regular_idx == -1:
                # Last segment
                segments.append((remaining, False))
                break
            elif optional_idx != -1 and (regular_idx == -1 or optional_idx < regular_idx):
                # Optional chain comes first
                segments.append((remaining[:optional_idx], True))
                remaining = remaining[optional_idx + 2 :]  # Skip ?.
            else:
                # Regular chain comes first
                segments.append((remaining[:regular_idx], False))
                remaining = remaining[regular_idx + 1 :]  # Skip .

        for i, (part, is_optional) in enumerate(segments):
            # Handle None in chain
            if current_obj is None:
                # Previous optional segment returned None, propagate it
                return None

            if not hasattr(current_obj, part):  # pyright: ignore[reportUnknownArgumentType]
                if is_optional:
                    # Optional attribute missing - return None
                    return None
                obj_type = type(current_obj).__name__  # pyright: ignore[reportUnknownArgumentType]
                traversed = ".".join(s[0] for s in segments[:i]) if i > 0 else "(root)"
                raise AttributeError(f"Cannot resolve ref('{self._name}'): '{part}' not found on {obj_type} (at {traversed})")

            current_obj = getattr(current_obj, part)  # pyright: ignore[reportUnknownArgumentType]

            # If it's a Variable, unwrap to .value
            if isinstance(current_obj, Variable):
                current_obj = current_obj.value  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            # For optional segments, None means we should return None for the whole chain
            if is_optional and current_obj is None:
                return None

        return current_obj  # pyright: ignore[reportUnknownVariableType]

    @override
    def __repr__(self) -> str:
        return f"ref({self._name!r})"


def ref(name: str) -> Ref:
    """Create a deferred reference to an attribute.

    Use this in new() to reference sibling fields or parent attributes
    that aren't available at class definition time.

    Args:
        name: The attribute path to reference. Supports:
              - "attr" - simple attribute on the same widget
              - "attr.nested.path" - nested attribute chain
              - "attr?.optional" - returns None if attr is None or missing
              - "#parent.attr" - attribute on the parent widget
              - "#parent.attr?.nested" - nested with optional chaining
              - "{attr}" - expression returning string
              - "Count: {len(items)}" - full expression language

    Returns:
        A Ref marker that will be resolved after field instantiation.
        For expression refs (containing {}), returns a string.

    Examples:
        # Reference a sibling field (same widget)
        _menu: TrayMenu = new()
        _tray: QSystemTrayIcon = new(contextMenu=ref("_menu"))

        # Reference a nested attribute
        _editor: QTextEdit = new()
        _label: QLabel = new(font=ref("_editor.document.defaultFont"))

        # Optional chaining - returns None instead of raising if missing/None
        _label: QLabel = new(text=ref("_config?.theme?.name"))

        # Reference a field on the parent widget
        _child: ChildWidget = new(model=ref("#parent._data_model"))

        # Expression refs - return strings
        _label: QLabel = new(text=ref("{_name}"))
        _label: QLabel = new(text=ref("Count: {len(_items)}"))
        _label: QLabel = new(text=ref("{_name.upper()}"))

    Note:
        - For path refs: If any attribute is a Variable[T], unwraps to .value
        - For expression refs: Uses QtPie's expression language, returns string
    """
    return Ref(name)
