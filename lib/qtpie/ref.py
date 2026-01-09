"""ref - Deferred attribute references for declarative field definitions."""

from typing import Any, override


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

    If any attribute in the chain is a Variable, resolves to .value (the underlying data).
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
        """
        self._name = name

    @property
    def name(self) -> str:
        """The attribute name this ref points to."""
        return self._name

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

        Raises:
            AttributeError: If a non-optional attribute in the chain doesn't exist
            ValueError: If #parent reference used but no parent provided
        """
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

    Returns:
        A Ref marker that will be resolved after field instantiation.

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

    Note:
        If any attribute in the chain is a Variable[T], the ref unwraps it
        to .value before continuing the traversal.
    """
    return Ref(name)
