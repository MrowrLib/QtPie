"""ReactiveFilterProxyModel - QSortFilterProxyModel with expression-based filtering and sorting."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, override

from observant import Observable, ObservableDict, ObservableList, ObservableSet
from qtpy.QtCore import QModelIndex, QPersistentModelIndex, QSortFilterProxyModel, Qt

from qtpie.bindings.format_binding import (
    _BUILTINS,  # pyright: ignore[reportPrivateUsage]
    _extract_ast_names,  # pyright: ignore[reportPrivateUsage]
    _get_observables_for_name,  # pyright: ignore[reportPrivateUsage]
    _parse_format_fields,  # pyright: ignore[reportPrivateUsage]
)

if TYPE_CHECKING:
    from qtpie.widget import Widget


# Names that come from the item, not the widget
_ITEM_CONTEXT_NAMES = frozenset({"item", "self"})


class ReactiveFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting ReactiveListModel/ReactiveTableModel/ReactiveTreeModel.

    Supports expression-based filtering:
        filter="{_search} in {name}"

    Supports expression-based sorting:
        sort="{age}"          # Sort by expression result
        sort="get_sort_key"   # Call widget method
        sort=lambda x: x.age  # Direct callable

    Where:
        - {_search} → widget's _search Variable value
        - {name}, {age} → each item's attribute
        - Filter expression evaluated per item → truthy = show, falsy = hide
        - Sort expression evaluated per item → returns comparable key

    Usage:
        proxy = ReactiveFilterProxyModel(
            filter_expr="{_search} in {name}",
            sort_key="{age}",
            widget=parent_widget,
            parent=view,
        )
        proxy.setSourceModel(reactive_list_model)
        view.setModel(proxy)
    """

    def __init__(
        self,
        parent: Any | None = None,
        *,
        filter_expr: str | Callable[[Any], bool] | None = None,
        sort_key: str | Callable[[Any], Any] | None = None,
        widget: Widget[Any] | None = None,
    ) -> None:
        """Initialize the filter proxy model.

        Args:
            parent: Parent QObject.
            filter_expr: Filter - expression "{_search} in {name}", method name, or callable.
            sort_key: Sort key - expression "{age}", method name "get_sort_key", or callable.
            widget: Parent widget for resolving Variables and methods.
        """
        super().__init__(parent)
        self._filter_expr: str | None = None
        self._filter_fn: Callable[[Any], bool] | None = None
        self._sort_key = sort_key
        self._sort_key_fn: Callable[[Any], Any] | None = None
        self._widget = widget
        self._widget_var_names: set[str] = set()
        self._item_var_names: set[str] = set()

        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setDynamicSortFilter(True)

        if filter_expr:
            self._setup_filter(filter_expr)

        if sort_key:
            self._setup_sort_key()

    def _setup_filter(self, filter_expr: str | Callable[[Any], bool]) -> None:
        """Set up the filter based on filter_expr parameter.

        Args:
            filter_expr: Filter - expression "{_search} in {name}", method name, or callable.
        """
        import logging

        logger = logging.getLogger(__name__)

        # Case 1: Callable - use directly
        if callable(filter_expr):
            self._filter_fn = filter_expr
            logger.debug("Filter: using callable directly")
            return

        # Case 2: String - could be expression "{...}" or method name "filter_items"
        if "{" in filter_expr and "}" in filter_expr:
            # Expression - parse and subscribe to Variables
            self._filter_expr = filter_expr
            self._parse_and_subscribe()
            logger.debug("Filter: using expression %r", filter_expr)
        else:
            # Method name - resolve from widget
            if self._widget is not None:
                method = getattr(self._widget, filter_expr, None)
                # DEBUG: Remove after fixing
                print(f"[FILTER DEBUG] widget={type(self._widget).__name__}, looking for {filter_expr!r}, found={method}")
                print(f"[FILTER DEBUG] widget has attrs: {[a for a in dir(self._widget) if not a.startswith('_')][:20]}...")
                logger.debug(
                    "Filter: resolving method %r from widget %s -> %s",
                    filter_expr,
                    type(self._widget).__name__,
                    method,
                )
                if method is not None and callable(method):
                    self._filter_fn = method  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
                else:
                    # Not a method - treat as simple attribute expression
                    logger.warning(
                        "Filter: method %r not found on %s, treating as expression",
                        filter_expr,
                        type(self._widget).__name__,
                    )
                    self._filter_expr = f"{{{filter_expr}}}"
                    self._parse_and_subscribe()
            else:
                # No widget - treat as simple attribute expression
                logger.warning("Filter: no widget provided, treating %r as expression", filter_expr)
                self._filter_expr = f"{{{filter_expr}}}"
                self._parse_and_subscribe()

    def _parse_and_subscribe(self) -> None:
        """Parse the filter expression and subscribe to widget Variables."""
        if not self._filter_expr or not self._widget:
            return

        from qtpie.variable import Variable

        # Parse the expression to find all variable names
        fields = _parse_format_fields(self._filter_expr)

        # Collect all variable names from fields
        all_names: set[str] = set()
        for field in fields:
            if field.is_expression:
                # Complex expression - use AST
                expr_names = _extract_ast_names(field.expression)
                # Filter out builtins
                all_names.update(expr_names - _BUILTINS)
            else:
                # Simple name
                expr = field.expression
                if not expr.startswith("#"):
                    root = expr.replace("?.", ".").split(".")[0]
                    all_names.add(root)

        # Classify names: widget Variables vs item attributes
        for name in all_names:
            # Check if this is a widget Variable
            attr = getattr(self._widget, name, None)
            if attr is None:
                # Try underscore prefix
                attr = getattr(self._widget, f"_{name}", None)
                if attr is not None:
                    # Store the actual attribute name for lookup
                    self._widget_var_names.add(f"_{name}")
                else:
                    # Assume it's an item attribute
                    self._item_var_names.add(name)
            elif isinstance(attr, Variable):
                self._widget_var_names.add(name)
            else:
                # It's a widget attribute but not a Variable - could be either
                # Check if item might have this attribute too (we can't know for sure)
                # Assume widget attribute takes precedence
                self._widget_var_names.add(name)

        # Subscribe to widget Variables for reactive updates
        for var_name in self._widget_var_names:
            obs_list = _get_observables_for_name(self._widget, var_name)
            for obs in obs_list:
                obs.on_change(self._on_variable_change)

    def _setup_sort_key(self) -> None:
        """Set up the sort key function based on sort_key parameter."""
        if self._sort_key is None:
            self._sort_key_fn = None
            return

        # Case 1: Callable - use directly
        if callable(self._sort_key):
            self._sort_key_fn = self._sort_key
            # Enable sorting
            self.setSortRole(Qt.ItemDataRole.UserRole)
            self.sort(0, Qt.SortOrder.AscendingOrder)
            return

        # Case 2: String - could be expression "{age}" or method name "get_sort_key"
        sort_str = self._sort_key
        if "{" in sort_str and "}" in sort_str:
            # Expression - create evaluator function
            self._sort_key_fn = self._create_expression_sort_key(sort_str)
        else:
            # Method name - resolve from widget
            if self._widget is not None:
                method = getattr(self._widget, sort_str, None)
                if method is not None and callable(method):
                    self._sort_key_fn = method  # pyright: ignore[reportUnknownMemberType]
                else:
                    # Not a method - try as simple attribute expression
                    self._sort_key_fn = self._create_expression_sort_key(f"{{{sort_str}}}")
            else:
                # No widget - try as simple attribute expression
                self._sort_key_fn = self._create_expression_sort_key(f"{{{sort_str}}}")

        # Enable sorting
        if self._sort_key_fn is not None:
            self.setSortRole(Qt.ItemDataRole.UserRole)
            self.sort(0, Qt.SortOrder.AscendingOrder)

    def _create_expression_sort_key(self, expr: str) -> Callable[[Any], Any]:
        """Create a sort key function from an expression string."""

        def sort_key(item: Any) -> Any:
            # Build context with item attributes
            context: dict[str, Any] = {"item": item, "self": item}

            # Add item attributes to context
            if hasattr(item, "__dict__"):
                context.update(vars(item))  # pyright: ignore[reportUnknownArgumentType]
            elif hasattr(item, "__dataclass_fields__"):
                from dataclasses import fields as dc_fields

                for field in dc_fields(item):  # pyright: ignore[reportArgumentType]
                    context[field.name] = getattr(item, field.name)

            # Parse and evaluate
            fields = _parse_format_fields(expr)

            # If single expression field, evaluate directly
            if len(fields) == 1 and expr == f"{{{fields[0].expression}}}":
                eval_expr = fields[0].expression
                eval_expr = eval_expr.replace("#self", "self")
                eval_expr = eval_expr.replace("#item", "item")
                try:
                    return eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                except Exception:
                    return None

            # Complex expression - build from template
            eval_parts: list[str] = []
            i = 0
            n = len(expr)
            last_end = 0
            while i < n:
                if expr[i] == "{":
                    if i + 1 < n and expr[i + 1] == "{":
                        eval_parts.append(expr[last_end:i])
                        eval_parts.append("{")
                        i += 2
                        last_end = i
                        continue
                    start = i + 1
                    brace_depth = 1
                    j = start
                    while j < n and brace_depth > 0:
                        if expr[j] == "{":
                            brace_depth += 1
                        elif expr[j] == "}":
                            brace_depth -= 1
                        j += 1
                    if brace_depth == 0:
                        eval_parts.append(expr[last_end:i])
                        field_expr = expr[start : j - 1]
                        field_expr = field_expr.replace("#self", "self")
                        field_expr = field_expr.replace("#item", "item")
                        eval_parts.append(field_expr)
                        i = j
                        last_end = i
                    else:
                        i += 1
                else:
                    i += 1
            eval_parts.append(expr[last_end:])
            final_expr = "".join(eval_parts)
            try:
                return eval(final_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
            except Exception:
                return None

        return sort_key

    @override
    def lessThan(
        self,
        left: QModelIndex | QPersistentModelIndex,
        right: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        """Compare two items for sorting using the sort key function."""
        if self._sort_key_fn is None:
            return super().lessThan(left, right)

        source_model = self.sourceModel()
        if source_model is None:  # pyright: ignore[reportUnnecessaryComparison]
            return super().lessThan(left, right)

        left_item = source_model.data(left, Qt.ItemDataRole.UserRole)
        right_item = source_model.data(right, Qt.ItemDataRole.UserRole)

        if left_item is None or right_item is None:
            return super().lessThan(left, right)

        try:
            left_key = self._sort_key_fn(left_item)
            right_key = self._sort_key_fn(right_item)
            # Handle None keys - put them at the end
            if left_key is None and right_key is None:
                return False
            if left_key is None:
                return False  # None goes after
            if right_key is None:
                return True  # Non-None goes before None
            return left_key < right_key  # pyright: ignore[reportUnknownVariableType]
        except Exception:
            return super().lessThan(left, right)

    def _on_variable_change(self, *_: Any) -> None:
        """Called when a subscribed widget Variable changes."""
        self._invalidate_rows_filter()

    def _invalidate_rows_filter(self) -> None:
        """Invalidate the filter using the non-deprecated API."""
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_filter_expression(self, expr: str | None) -> None:
        """Set a new filter expression."""
        self._filter_expr = expr
        self._widget_var_names.clear()
        self._item_var_names.clear()
        if expr:
            self._parse_and_subscribe()
        self._invalidate_rows_filter()

    def _evaluate_filter(self, item: Any) -> bool:
        """Evaluate the filter expression for an item."""
        # Case 1: Callable filter function
        if self._filter_fn is not None:
            try:
                return bool(self._filter_fn(item))
            except Exception:
                return False

        # Case 2: No filter - show all
        if not self._filter_expr:
            return True

        from qtpie.variable import Variable

        # Build evaluation context
        context: dict[str, Any] = {}

        # Add item reference
        context["item"] = item
        context["self"] = item

        # Add widget Variable values
        if self._widget:
            for var_name in self._widget_var_names:
                attr = getattr(self._widget, var_name, None)
                if attr is None and not var_name.startswith("_"):
                    attr = getattr(self._widget, f"_{var_name}", None)

                # Use original var_name as context key (matches expression)
                if isinstance(attr, Variable):
                    # Get the observable value
                    # Variable[T].observable has Unknown type param
                    obs: Any = attr.observable  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    if isinstance(obs, Observable):
                        context[var_name] = obs.get()
                    elif isinstance(obs, ObservableList):
                        context[var_name] = obs.to_list()
                    elif isinstance(obs, ObservableDict):
                        context[var_name] = obs.to_dict()
                    elif isinstance(obs, ObservableSet):
                        context[var_name] = obs.to_set()
                    else:  # ObservableProxy
                        context[var_name] = obs.unwrap()  # pyright: ignore[reportUnknownMemberType]
                else:
                    context[var_name] = attr

        # Add item attributes
        for attr_name in self._item_var_names:
            if hasattr(item, attr_name):
                context[attr_name] = getattr(item, attr_name)

        # Build the expression by replacing placeholders
        expr = self._filter_expr

        # Parse and evaluate
        fields = _parse_format_fields(expr)

        # If single expression field spanning whole string, evaluate directly
        if len(fields) == 1 and expr == f"{{{fields[0].expression}}}":
            eval_expr = fields[0].expression
            eval_expr = eval_expr.replace("#self", "self")
            eval_expr = eval_expr.replace("#item", "item")
            try:
                result = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                return bool(result)
            except Exception:
                return False

        # Complex case: build expression from template
        # For filter expressions, we expect a single boolean expression
        # e.g., "{_search} in {name}" should become "_search in name"
        eval_parts: list[str] = []
        last_end = 0

        # Rebuild expression with variable substitution
        i = 0
        n = len(expr)
        while i < n:
            if expr[i] == "{":
                if i + 1 < n and expr[i + 1] == "{":
                    eval_parts.append(expr[last_end:i])
                    eval_parts.append("{")
                    i += 2
                    last_end = i
                    continue

                # Find matching brace
                start = i + 1
                brace_depth = 1
                j = start
                while j < n and brace_depth > 0:
                    if expr[j] == "{":
                        brace_depth += 1
                    elif expr[j] == "}":
                        brace_depth -= 1
                    j += 1

                if brace_depth == 0:
                    # Add literal before this
                    eval_parts.append(expr[last_end:i])

                    # Get the expression inside braces
                    field_expr = expr[start : j - 1]
                    # Handle special placeholders
                    field_expr = field_expr.replace("#self", "self")
                    field_expr = field_expr.replace("#item", "item")
                    eval_parts.append(field_expr)

                    i = j
                    last_end = i
                else:
                    i += 1
            else:
                i += 1

        # Add remaining literal
        eval_parts.append(expr[last_end:])

        # Join and evaluate
        final_expr = "".join(eval_parts)

        try:
            result = eval(final_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
            return bool(result)
        except Exception:
            return False

    @override
    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        """Determine if a row should be shown based on filter expression or callable."""
        # No filter = show all
        if not self._filter_expr and self._filter_fn is None:
            return True

        source_model = self.sourceModel()
        if source_model is None:  # pyright: ignore[reportUnnecessaryComparison]
            return True

        # Get the item from the source model
        index = source_model.index(source_row, 0, source_parent)
        item = source_model.data(index, Qt.ItemDataRole.UserRole)

        if item is None:
            return False

        return self._evaluate_filter(item)
