# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportPrivateUsage=false
"""Signal expression handler factory shared across QtPie modules."""

from collections.abc import Callable
from typing import Any

from ..utils.common import is_signal


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
    """
    from ..bindings.format_binding import _BUILTINS, _extract_ast_names, _parse_format_fields
    from ..variable import Variable

    # Parse the expression to get the inner content
    fields = _parse_format_fields(expression)
    if not fields:
        raise ValueError(f"Invalid signal expression: {expression}")

    # We expect a single expression field
    expr = fields[0].expression

    # Check if expression uses special placeholders
    uses_args = "#args" in expr
    uses_self = any(placeholder in expr for placeholder in self_placeholders)

    # Replace special placeholders before AST extraction (they're not valid Python)
    expr_for_ast = expr
    if uses_args:
        expr_for_ast = expr_for_ast.replace("#args", "_signal_args_placeholder_")
    if uses_self:
        for placeholder in self_placeholders:
            expr_for_ast = expr_for_ast.replace(placeholder, "_context_ref_")

    # Extract variable names from the expression for context building
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
            # Try exact match first
            if hasattr(context_obj, var_name):
                raw_attr: Any = getattr(context_obj, var_name)
                if isinstance(raw_attr, Variable):
                    context[var_name] = raw_attr.value
                elif is_signal(raw_attr):
                    # Wrap signal so it can be called directly (calls .emit())
                    context[var_name] = raw_attr.emit
                else:
                    context[var_name] = raw_attr
            # Try underscore fallback
            elif hasattr(context_obj, f"_{var_name}"):
                raw_attr = getattr(context_obj, f"_{var_name}")
                if isinstance(raw_attr, Variable):
                    context[var_name] = raw_attr.value
                elif is_signal(raw_attr):
                    context[var_name] = raw_attr.emit
                else:
                    context[var_name] = raw_attr

        # Replace special placeholders
        eval_expr = expr
        if uses_args:
            eval_expr = eval_expr.replace("#args", "*signal_args")
        if uses_self:
            for placeholder in self_placeholders:
                eval_expr = eval_expr.replace(placeholder, "context_ref")

        # Evaluate the expression
        try:
            result = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
            return result
        except Exception as e:
            raise RuntimeError(f"Error evaluating signal expression '{expression}': {e}") from e

    return handler
