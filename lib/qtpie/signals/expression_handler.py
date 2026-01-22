# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportPrivateUsage=false
"""Signal expression handler factory shared across QtPie modules."""

from collections.abc import Callable
from typing import Any

from ..utils.common import is_signal


def _resolve_var_for_expression(context_obj: Any, var_name: str) -> Any | None:
    """Resolve a variable for signal expression context, walking parent hierarchy.

    Returns the resolved value ready for use in eval context:
    - Variable -> unwrapped value
    - Signal -> .emit method (so it can be called directly)
    - Other -> raw value

    Returns None if not found.
    """
    from ..variable import Variable

    # Try on context_obj itself (exact name, then underscore prefix)
    for attr_name in [var_name, f"_{var_name}"]:
        if hasattr(context_obj, attr_name):
            raw_attr: Any = getattr(context_obj, attr_name)
            if isinstance(raw_attr, Variable):
                return raw_attr.value
            elif is_signal(raw_attr):
                return raw_attr.emit
            else:
                return raw_attr

    # Walk parent hierarchy
    if hasattr(context_obj, "parent") and callable(context_obj.parent):
        current: Any = context_obj
        while True:
            parent_obj: Any = current.parent() if hasattr(current, "parent") and callable(current.parent) else None
            if parent_obj is None:
                break

            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(parent_obj, attr_name):
                    raw_attr = getattr(parent_obj, attr_name)
                    if isinstance(raw_attr, Variable):
                        return raw_attr.value
                    elif is_signal(raw_attr):
                        return raw_attr.emit
                    else:
                        return raw_attr

            current = parent_obj

        # Check QApplication.instance() for app-level Variables
        from qtpy.QtWidgets import QApplication

        app_instance = QApplication.instance()
        if app_instance is not None:
            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(app_instance, attr_name):
                    raw_attr = getattr(app_instance, attr_name)
                    if isinstance(raw_attr, Variable):
                        return raw_attr.value
                    elif is_signal(raw_attr):
                        return raw_attr.emit
                    else:
                        return raw_attr

    return None


def _resolve_variable_object(context_obj: Any, var_name: str) -> Any | None:
    """Resolve a Variable object (not its value) for assignment support.

    Returns the Variable object itself, not its value.
    Returns None if not found or not a Variable.
    """
    from ..variable import Variable

    # Try on context_obj itself (exact name, then underscore prefix)
    for attr_name in [var_name, f"_{var_name}"]:
        if hasattr(context_obj, attr_name):
            raw_attr: Any = getattr(context_obj, attr_name)
            if isinstance(raw_attr, Variable):
                return raw_attr

    # Walk parent hierarchy
    if hasattr(context_obj, "parent") and callable(context_obj.parent):
        current: Any = context_obj
        while True:
            parent_obj: Any = current.parent() if hasattr(current, "parent") and callable(current.parent) else None
            if parent_obj is None:
                break

            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(parent_obj, attr_name):
                    raw_attr = getattr(parent_obj, attr_name)
                    if isinstance(raw_attr, Variable):
                        return raw_attr

            current = parent_obj

        # Check QApplication.instance() for app-level Variables
        from qtpy.QtWidgets import QApplication

        app_instance = QApplication.instance()
        if app_instance is not None:
            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(app_instance, attr_name):
                    raw_attr = getattr(app_instance, attr_name)
                    if isinstance(raw_attr, Variable):
                        return raw_attr

    return None


def _is_statement(code: str) -> bool:
    """Check if code is a statement (vs expression).

    Statements include assignments, augmented assignments, etc.
    """
    import ast

    try:
        # Try to parse as expression
        ast.parse(code, mode="eval")
        return False
    except SyntaxError:
        # Not a valid expression, might be a statement
        try:
            ast.parse(code, mode="exec")
            return True
        except SyntaxError:
            return False


def _extract_assignment_target(code: str) -> tuple[str, str, str] | None:
    """Extract assignment target, operator, and value from assignment statement.

    Returns (target_name, operator, value_expr) or None if not an assignment.
    Handles: x = 1, x += 1, x -= 1, etc.
    """
    import ast

    try:
        tree = ast.parse(code, mode="exec")
        if not tree.body:
            return None

        stmt = tree.body[0]

        # Simple assignment: x = value
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                # Get the value expression as string
                value_expr = ast.unparse(stmt.value)
                return (target.id, "=", value_expr)

        # Augmented assignment: x += value, x -= value, etc.
        if isinstance(stmt, ast.AugAssign):
            target = stmt.target
            if isinstance(target, ast.Name):
                # Map AST operator to string
                op_map = {
                    ast.Add: "+=",
                    ast.Sub: "-=",
                    ast.Mult: "*=",
                    ast.Div: "/=",
                    ast.Mod: "%=",
                    ast.Pow: "**=",
                    ast.FloorDiv: "//=",
                    ast.BitOr: "|=",
                    ast.BitXor: "^=",
                    ast.BitAnd: "&=",
                    ast.LShift: "<<=",
                    ast.RShift: ">>=",
                }
                op_type = type(stmt.op)
                op_str = op_map[op_type] if op_type in op_map else "?="
                value_expr = ast.unparse(stmt.value)
                return (target.id, op_str, value_expr)

        return None
    except SyntaxError:
        return None


def create_signal_expression_handler(
    context_obj: Any,
    expression: str,
    self_placeholders: list[str],
) -> Callable[..., Any]:
    """Create a signal handler from an expression string like "{my_signal(123)}".

    This is a generic factory that works for Widget, Window, Menu, and App.

    Args:
        context_obj: The object (widget/window/menu/app) that provides the context.
        expression: The expression string like "{on_clicked()}" or "{my_signal(123)}".
        self_placeholders: List of placeholders that refer to context_obj
                          (e.g., ["#widget", "#self"] for Widget).

    Returns:
        A handler function that can be connected to a Qt signal.

    The expression is evaluated in the context_obj's namespace when the signal fires.
    Supports:
        - Method calls: {on_clicked()}, {handle_value(123)}
        - Signal emissions: {my_signal()}, {value_changed(42)}
        - Full Python expressions with context_obj variables
        - #args placeholder to pass signal arguments: {handle_click(#args)}
        - Self placeholders for the context_obj instance
        - Assignments to Variables: {test_var = 123}, {count += 1}
    """
    from ..bindings.format_binding import _BUILTINS, _extract_ast_names, _parse_format_fields

    # Parse the expression to get the inner content
    fields = _parse_format_fields(expression)
    if not fields:
        raise ValueError(f"Invalid signal expression: {expression}")

    # We expect a single expression field
    expr = fields[0].expression

    # Check if expression uses special placeholders
    uses_args = "#args" in expr
    uses_self = any(placeholder in expr for placeholder in self_placeholders)

    # Check if this is a statement (assignment, etc.)
    is_stmt = _is_statement(expr)

    # For assignments, check if target is a Variable
    assignment_info = _extract_assignment_target(expr) if is_stmt else None

    # Replace special placeholders before AST extraction (they're not valid Python)
    expr_for_ast = expr
    if uses_args:
        expr_for_ast = expr_for_ast.replace("#args", "_signal_args_placeholder_")
    if uses_self:
        for placeholder in self_placeholders:
            expr_for_ast = expr_for_ast.replace(placeholder, "_context_ref_")

    # Extract variable names from the expression for context building
    # For assignments, we also need to extract names from the value expression
    if assignment_info:
        _, _, value_expr = assignment_info
        value_expr_for_ast = value_expr
        if uses_args:
            value_expr_for_ast = value_expr_for_ast.replace("#args", "_signal_args_placeholder_")
        if uses_self:
            for placeholder in self_placeholders:
                value_expr_for_ast = value_expr_for_ast.replace(placeholder, "_context_ref_")
        var_names = _extract_ast_names(value_expr_for_ast) - _BUILTINS
    else:
        var_names = _extract_ast_names(expr_for_ast) - _BUILTINS
    # Remove placeholder names we added
    var_names.discard("_signal_args_placeholder_")
    var_names.discard("_context_ref_")

    def handler(*signal_args: Any) -> Any:
        # Build context with context_obj's variables
        context: dict[str, Any] = {}

        # Add context_obj reference for self placeholders
        if uses_self:
            context["context_ref"] = context_obj

        # Add #args support
        if uses_args:
            context["signal_args"] = signal_args

        # Add all variable values to context
        for var_name in var_names:
            resolved = _resolve_var_for_expression(context_obj, var_name)
            if resolved is not None:
                context[var_name] = resolved

        # Replace special placeholders
        eval_expr = expr
        if uses_args:
            eval_expr = eval_expr.replace("#args", "*signal_args")
        if uses_self:
            for placeholder in self_placeholders:
                eval_expr = eval_expr.replace(placeholder, "context_ref")

        # Execute/evaluate the expression
        try:
            if is_stmt and assignment_info:
                # Handle assignment to Variable specially
                target_name, operator, value_expr = assignment_info
                var_obj = _resolve_variable_object(context_obj, target_name)

                if var_obj is not None:
                    # Target is a Variable - update its .value
                    # Evaluate the value expression
                    new_value = eval(value_expr, {"__builtins__": __builtins__}, context)  # noqa: S307

                    if operator == "=":
                        var_obj.value = new_value
                    elif operator == "+=":
                        var_obj.value = var_obj.value + new_value
                    elif operator == "-=":
                        var_obj.value = var_obj.value - new_value
                    elif operator == "*=":
                        var_obj.value = var_obj.value * new_value
                    elif operator == "/=":
                        var_obj.value = var_obj.value / new_value
                    elif operator == "//=":
                        var_obj.value = var_obj.value // new_value
                    elif operator == "%=":
                        var_obj.value = var_obj.value % new_value
                    elif operator == "**=":
                        var_obj.value = var_obj.value**new_value
                    elif operator == "|=":
                        var_obj.value = var_obj.value | new_value
                    elif operator == "&=":
                        var_obj.value = var_obj.value & new_value
                    elif operator == "^=":
                        var_obj.value = var_obj.value ^ new_value
                    elif operator == "<<=":
                        var_obj.value = var_obj.value << new_value
                    elif operator == ">>=":
                        var_obj.value = var_obj.value >> new_value
                    return None
                else:
                    # Not a Variable, use exec for regular statement
                    exec(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S102
                    return None
            elif is_stmt:
                # Statement but not a simple assignment we can handle
                exec(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S102
                return None
            else:
                # Regular expression
                result = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                return result
        except Exception as e:
            raise RuntimeError(f"Error evaluating signal expression '{expression}': {e}") from e

    return handler
