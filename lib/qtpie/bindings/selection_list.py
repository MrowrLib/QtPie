"""Selection bindings for QComboBox and QListView."""

import logging
from typing import Any

from qtpy.QtWidgets import QWidget

logger = logging.getLogger("qtpie.bindings")


def setup_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveListModel
    selected_index_path: str | None,
    selected_item_path: str | None,
    selected_indexes_path: str | None = None,
    selected_items_list_path: str | None = None,
    selected_widget_path: str | None = None,
    selected_text_path: str | None = None,
    resolve_or_create_variable_fn: Any = None,  # Callable to resolve/create variables
    root_variable: Any = None,  # Root Variable for nested paths (passed from model_binding)
) -> None:
    """Set up two-way selection bindings for model widgets.

    Args:
        host: The Widget/Window instance containing the Variables
        widget: The model widget (QComboBox, QListView, etc.)
        model: The ReactiveListModel backing the widget
        selected_index_path: Variable path for index binding (e.g., "_selected_idx")
        selected_item_path: Variable path for item binding (e.g., "_selected_item")
        selected_indexes_path: Variable path for multi-index binding (QListView only)
        selected_items_list_path: Variable path for multi-item binding (QListView only)
        selected_widget_path: Variable path for embedded widget binding (e.g., "_selected_widget")
        selected_text_path: Variable path for text binding - matches by display text (e.g., "_selected_name")
        resolve_or_create_variable_fn: Function to resolve/create variables (injected from apply.py)
        root_variable: Root Variable for nested binding paths (e.g., workspace for "workspace?.active_env")
    """
    has_single = selected_index_path is not None or selected_item_path is not None or selected_text_path is not None
    has_multi = selected_indexes_path is not None or selected_items_list_path is not None
    has_widget = selected_widget_path is not None
    if not has_single and not has_multi and not has_widget:
        return

    from observant import Observable, ObservableProxy

    from qtpie.variable import Variable as VarType

    # Resolve the Variables (creating them if they're bare annotations)
    index_var: VarType[int] | None = None
    item_var: VarType[Any] | None = None
    indexes_var: VarType[list[int]] | None = None
    items_list_var: VarType[list[Any]] | None = None
    widget_var: VarType[Any] | None = None

    if selected_index_path is not None:
        source = resolve_or_create_variable_fn(host, selected_index_path, int)
        if isinstance(source, VarType):
            index_var = source  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(source, (Observable, ObservableProxy)):
            index_var = source  # type: ignore[assignment] - Observable/Proxy has .value and .on_change

    if selected_item_path is not None:
        source = resolve_or_create_variable_fn(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(source, (Observable, ObservableProxy)):
            item_var = source  # type: ignore[assignment] - Observable/Proxy has .value and .on_change

    if selected_indexes_path is not None:
        source = resolve_or_create_variable_fn(host, selected_indexes_path, None)
        if isinstance(source, VarType):
            indexes_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_items_list_path is not None:
        source = resolve_or_create_variable_fn(host, selected_items_list_path, None)
        if isinstance(source, VarType):
            items_list_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_widget_path is not None:
        source = resolve_or_create_variable_fn(host, selected_widget_path, None)
        if isinstance(source, VarType):
            widget_var = source  # pyright: ignore[reportUnknownVariableType]

    text_var: VarType[str] | None = None

    if selected_text_path is not None:
        source = resolve_or_create_variable_fn(host, selected_text_path, str)
        if isinstance(source, VarType):
            text_var = source  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(source, (Observable, ObservableProxy)):
            text_var = source  # type: ignore[assignment] - Observable/Proxy has .value and .on_change  # pyright: ignore[reportUnknownVariableType]

    # ALWAYS call _setup_selection_bindings_impl to connect the signal handler early.
    # This ensures the selection binding handler is connected BEFORE user's signal handlers
    # (which are connected later in _connect_signals). The handler uses a mutable container
    # so it can access Variables that are resolved later when bindings are reapplied.
    _setup_selection_bindings_impl(
        host,
        widget,
        model,
        index_var,
        item_var,
        indexes_var,
        items_list_var,
        widget_var,
        text_var,
        root_variable=root_variable,
        index_var_path=selected_index_path,
        item_var_path=selected_item_path,
        text_var_path=selected_text_path,
        resolve_or_create_variable_fn=resolve_or_create_variable_fn,
    )


def _setup_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveListModel
    index_var: Any | None,  # Variable[int] | None
    item_var: Any | None,  # Variable[Any] | None
    indexes_var: Any | None,  # Variable[list[int]] | None
    items_list_var: Any | None,  # Variable[list[Any]] | None
    widget_var: Any | None = None,  # Variable[QWidget | None] | None
    text_var: Any | None = None,  # Variable[str] | None - matches by display text
    root_variable: Any | None = None,  # Root Variable for nested paths (from model_binding)
    index_var_path: str | None = None,  # Original path for re-resolution
    item_var_path: str | None = None,  # Original path for re-resolution
    text_var_path: str | None = None,  # Original path for re-resolution
    resolve_or_create_variable_fn: Any | None = None,  # For re-resolving nested paths
) -> None:
    """Implementation of selection bindings (called after Variables are resolved)."""
    from observant import Observable, ObservableProxy
    from qtpy.QtCore import QModelIndex, Qt
    from qtpy.QtWidgets import QComboBox

    # Use mutable containers for model and item_var so they can be updated when
    # record changes. This allows the same signal handler to use updated references
    # without needing to disconnect/reconnect (which would mess up handler ordering).
    handler_key = f"selection_{id(widget)}"
    qtpie_state = getattr(host, "_qtpie", None)
    handler_connected = False

    # Container for model, index_var, item_var, and text_var - allows updating references when bindings reapply
    binding_container: dict[str, Any] = {
        "model": model,
        "index_var": index_var,
        "item_var": item_var,
        "text_var": text_var,
        "widget_var": widget_var,
        "is_item_observable": isinstance(item_var, Observable) if item_var is not None else False,
        "is_item_proxy": isinstance(item_var, ObservableProxy) if item_var is not None else False,
        "is_index_observable": isinstance(index_var, Observable) if index_var is not None else False,
        "is_index_proxy": isinstance(index_var, ObservableProxy) if index_var is not None else False,
        "connected": False,
    }

    if qtpie_state is not None:
        handlers_dict: dict[str, Any] | None = getattr(qtpie_state, "_handlers", None)
        if handlers_dict is not None:
            existing = handlers_dict.get(handler_key)
            # Check if it's a dict (our new format) vs a function (old QListView format)
            if existing is not None and isinstance(existing, dict):
                existing_dict: dict[str, Any] = existing  # pyright: ignore[reportUnknownVariableType]
                # Update existing container with new model and Variables - the old signal
                # handler's closures will now use these updated references
                existing_dict["model"] = model
                existing_dict["index_var"] = index_var
                existing_dict["item_var"] = item_var
                existing_dict["text_var"] = text_var
                existing_dict["is_item_observable"] = isinstance(item_var, Observable) if item_var is not None else False
                existing_dict["is_item_proxy"] = isinstance(item_var, ObservableProxy) if item_var is not None else False
                existing_dict["is_index_observable"] = isinstance(index_var, Observable) if index_var is not None else False
                existing_dict["is_index_proxy"] = isinstance(index_var, ObservableProxy) if index_var is not None else False
                binding_container = existing_dict
                handler_connected = bool(existing_dict.get("connected", False))
            else:
                # First time or old format - store container
                handlers_dict[handler_key] = binding_container

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Helpers to get/set index_var value (handles Variable, Observable, and ObservableProxy)
    def get_index_var_value() -> int | None:
        current_index_var = binding_container["index_var"]
        if current_index_var is None:
            return None
        if binding_container["is_index_observable"]:
            return current_index_var.get()  # pyright: ignore[reportUnknownMemberType]
        if binding_container["is_index_proxy"]:
            return current_index_var.unwrap()  # pyright: ignore[reportUnknownMemberType]
        return current_index_var.value  # pyright: ignore[reportUnknownMemberType]

    def set_index_var_value(val: int) -> None:
        current_index_var = binding_container["index_var"]
        if current_index_var is None:
            return
        if binding_container["is_index_observable"]:
            current_index_var.set(val)  # pyright: ignore[reportUnknownMemberType]
        elif binding_container["is_index_proxy"]:
            current_index_var.replace_target(val)  # pyright: ignore[reportUnknownMemberType]
        else:
            current_index_var.value = val  # pyright: ignore[reportUnknownMemberType]

    # Helpers to get/set item_var value (handles Variable, Observable, and ObservableProxy)
    def get_item_var_value() -> Any:
        current_item_var = binding_container["item_var"]
        if current_item_var is None:
            return None
        if binding_container["is_item_observable"]:
            return current_item_var.get()  # pyright: ignore[reportUnknownMemberType]
        if binding_container["is_item_proxy"]:
            return current_item_var.unwrap()  # pyright: ignore[reportUnknownMemberType]
        return current_item_var.value  # pyright: ignore[reportUnknownMemberType]

    # Helper to check if model is still valid AND still the current model on the widget
    def is_model_valid() -> bool:
        current_model_ref = binding_container["model"]
        try:
            current_model_ref.rowCount()  # Will raise RuntimeError if deleted
            # Also check if this model is still the widget's current model
            get_model = getattr(widget, "model", None)
            if get_model is not None:
                widget_model: Any = get_model()
                return widget_model is current_model_ref
            return True  # Widget doesn't have model() method, assume valid
        except RuntimeError:
            return False

    # Import PROXY_ROLE for getting ObservableProxy from model
    from qtpie.models.reactive_list_model import PROXY_ROLE

    # Helper to get item at index via model's UserRole
    def get_item_at_index(idx: int) -> Any:
        try:
            current_model = binding_container["model"]
            if idx < 0 or idx >= current_model.rowCount():
                return None
            model_index = current_model.index(idx, 0)
            return current_model.data(model_index, Qt.ItemDataRole.UserRole)
        except RuntimeError:
            # Model was deleted
            return None

    # Helper to get ObservableProxy at index via model's PROXY_ROLE
    def get_proxy_at_index(idx: int) -> ObservableProxy[Any] | None:
        from typing import cast

        try:
            current_model = binding_container["model"]
            if idx < 0 or idx >= current_model.rowCount():
                return None
            model_index = current_model.index(idx, 0)
            proxy: Any = current_model.data(model_index, PROXY_ROLE)
            if isinstance(proxy, ObservableProxy):
                return cast(ObservableProxy[Any], proxy)
            return None
        except (RuntimeError, AttributeError):
            # Model was deleted or doesn't support PROXY_ROLE
            return None

    # Helper to find index of item
    def find_index_of_item(item: Any) -> int:
        try:
            current_model = binding_container["model"]
            for i in range(current_model.rowCount()):
                if get_item_at_index(i) == item:
                    return i
            return -1
        except RuntimeError:
            # Model was deleted
            return -1

    # Helper to get the display text at index (uses model's format function)
    def get_display_text_at_index(idx: int) -> str | None:
        try:
            current_model = binding_container["model"]
            if idx < 0 or idx >= current_model.rowCount():
                return None
            model_index = current_model.index(idx, 0)
            # Get the display text (Qt.DisplayRole)
            text = current_model.data(model_index, Qt.ItemDataRole.DisplayRole)
            return str(text) if text is not None else None
        except RuntimeError:
            # Model was deleted
            return None

    # Helper to find index by display text (matches the formatted text shown in widget)
    def find_index_by_display_text(text: str | None) -> int:
        if text is None:
            return -1
        try:
            current_model = binding_container["model"]
            for i in range(current_model.rowCount()):
                display_text = get_display_text_at_index(i)
                if display_text == text:
                    return i
            return -1
        except RuntimeError:
            # Model was deleted
            return -1

    # Detect widget type and set up appropriate bindings
    # QComboBox: currentIndex() returns int, setCurrentIndex(int), currentIndexChanged signal
    # QListView/QTableView: use selectionModel, currentIndex() returns QModelIndex
    is_combobox = isinstance(widget, QComboBox)

    if is_combobox:
        # QComboBox-specific setup
        set_current_index_fn = getattr(widget, "setCurrentIndex", None)
        current_index_changed = getattr(widget, "currentIndexChanged", None)
        current_widget_index_fn = getattr(widget, "currentIndex", None)

        # Get the current widget index (will sync Variables from this if they're None)
        current_widget_idx: int = current_widget_index_fn() if current_widget_index_fn else 0

        if index_var is not None and set_current_index_fn is not None:
            initial_idx = get_index_var_value()
            # Variable[int] can have None value if no default provided
            if initial_idx is not None:  # pyright: ignore[reportUnnecessaryComparison]
                set_current_index_fn(initial_idx)
                current_widget_idx = initial_idx  # Update for item_var sync below
            else:
                # Sync Variable to widget's current state
                set_index_var_value(current_widget_idx)

        def set_item_var_value(val: Any, idx: int = -1) -> None:
            """Set the item variable value, using replace_wrapper for complex objects.

            For Variables with ObservableProxy wrappers AND complex object values
            (dataclasses, custom classes), we use replace_wrapper() with the model's
            cached proxy to enable per-item dirty state tracking.

            Variable.replace_wrapper() preserves on_change callbacks by re-registering
            them on the new wrapper.
            """
            from dataclasses import is_dataclass
            from enum import Enum

            current_item_var = binding_container["item_var"]
            if current_item_var is None:
                return
            if binding_container["is_item_observable"]:
                current_item_var.set(val)
            elif binding_container["is_item_proxy"]:
                current_item_var.replace_target(val)
            else:
                # Only use replace_wrapper if:
                # 1. Variable uses an ObservableProxy wrapper
                # 2. The value is a "complex object" (dataclass or custom class with __dict__)
                proxy = get_proxy_at_index(idx) if idx >= 0 else None
                current_wrapper = getattr(current_item_var, "_wrapper", None)

                # Check if the value is a "complex object" that benefits from proxy sharing
                is_complex_object = False
                if val is not None:
                    val_type = type(val)  # pyright: ignore[reportUnknownArgumentType,reportUnknownVariableType]
                    is_dataclass_instance = is_dataclass(val) and not isinstance(val, type)
                    is_enum = isinstance(val, Enum)
                    is_builtin = val_type.__module__ == "builtins"
                    has_dict = hasattr(val, "__dict__")
                    is_complex_object = is_dataclass_instance or (has_dict and not is_enum and not is_builtin)

                if proxy is not None and is_complex_object and hasattr(current_item_var, "replace_wrapper") and isinstance(current_wrapper, ObservableProxy):
                    current_item_var.replace_wrapper(proxy)
                else:
                    current_item_var.value = val

        if item_var is not None:
            initial_item = get_item_var_value()
            if initial_item is not None:
                # Set widget to match item if index didn't already set it
                if index_var is None and set_current_index_fn is not None:
                    idx = find_index_of_item(initial_item)
                    if idx >= 0:
                        set_current_index_fn(idx)
            else:
                # Sync Variable/Observable to widget's current selection
                new_val = get_item_at_index(current_widget_idx)
                set_item_var_value(new_val, current_widget_idx)

        # text_var: Variable[str] or Observable[str] - matches by display text (formatted text shown in combo)
        # Track whether text_var is Observable (uses .get()/.set()) vs Variable (uses .value)
        binding_container["is_text_observable"] = isinstance(text_var, Observable) if text_var is not None else False

        def get_text_var_value() -> str | None:
            current_text_var = binding_container.get("text_var")
            if current_text_var is None:
                return None
            if binding_container.get("is_text_observable", False):
                return current_text_var.get()  # type: ignore[no-any-return]
            return current_text_var.value  # type: ignore[no-any-return]

        def set_text_var_value(val: str | None) -> None:
            current_text_var = binding_container.get("text_var")
            if current_text_var is None:
                return
            if binding_container.get("is_text_observable", False):
                current_text_var.set(val)
            else:
                current_text_var.value = val

        if text_var is not None:
            initial_text = get_text_var_value()

            # Store the intended text value - this is what we want to match when items are added later.
            # We track this separately because widget auto-selection may overwrite text_var before
            # rowsInserted fires.
            binding_container["intended_text"] = initial_text

            if initial_text is not None and initial_text != "":
                # Set widget to match text if index/item didn't already set it
                if index_var is None and item_var is None and set_current_index_fn is not None:
                    idx = find_index_by_display_text(initial_text)
                    if idx >= 0:
                        set_current_index_fn(idx)
                        current_widget_idx = idx
                        # Clear intended_text since we found a match
                        binding_container["intended_text"] = None
            else:
                # Sync text Variable to widget's current selection's display text
                display_text = get_display_text_at_index(current_widget_idx)
                if display_text is not None:
                    set_text_var_value(display_text)
                    binding_container["intended_text"] = None

        # Variable → Widget binding (and cross-update between index/item vars)
        if index_var is not None and set_current_index_fn is not None:

            def on_index_var_change_combo(new_idx: int) -> None:
                if not is_model_valid():
                    return
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    set_current_index_fn(new_idx)
                    # Also update item_var if both bindings are present
                    set_item_var_value(get_item_at_index(new_idx), new_idx)
                finally:
                    updating["flag"] = False

            index_var.on_change(on_index_var_change_combo)

            # For nested paths like "workspace?.selected_index", subscribe to ROOT Variable
            if root_variable is not None and index_var_path is not None and resolve_or_create_variable_fn is not None:
                from qtpie.variable import Variable as VarType

                root_subscribed_key = f"combo_index_root_subscribed_{id(widget)}"
                if not binding_container.get(root_subscribed_key, False):
                    binding_container[root_subscribed_key] = True

                    def on_root_variable_change_combo_index(*_args: Any) -> None:
                        """Re-resolve index_var when root Variable changes."""
                        if updating["flag"]:
                            return
                        assert index_var_path is not None
                        assert resolve_or_create_variable_fn is not None
                        assert set_current_index_fn is not None
                        new_source = resolve_or_create_variable_fn(host, index_var_path, int)
                        if new_source is None:
                            return

                        new_idx: int | None = None
                        if isinstance(new_source, VarType):
                            new_idx = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                        elif isinstance(new_source, (Observable, ObservableProxy)):
                            val = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]
                            new_idx = val if isinstance(val, int) else None

                        if new_idx is not None and new_idx >= 0:
                            updating["flag"] = True
                            try:
                                set_current_index_fn(new_idx)
                            finally:
                                updating["flag"] = False

                    root_variable.on_change(on_root_variable_change_combo_index)

        if item_var is not None and set_current_index_fn is not None:

            def on_item_var_change_combo(*_args: Any) -> None:
                # Note: Observable passes value, ObservableProxy passes nothing
                if not is_model_valid():
                    return
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    new_item = get_item_var_value()
                    idx = find_index_of_item(new_item)
                    if idx >= 0:
                        set_current_index_fn(idx)
                        # Also update index_var if both bindings are present
                        if index_var is not None:
                            set_index_var_value(idx)
                finally:
                    updating["flag"] = False

            item_var.on_change(on_item_var_change_combo)

            # For nested paths like "workspace?.selected_item", subscribe to ROOT Variable
            if root_variable is not None and item_var_path is not None and resolve_or_create_variable_fn is not None:
                from qtpie.variable import Variable as VarType

                root_subscribed_key = f"combo_item_root_subscribed_{id(widget)}"
                if not binding_container.get(root_subscribed_key, False):
                    binding_container[root_subscribed_key] = True

                    def on_root_variable_change_combo_item(*_args: Any) -> None:
                        """Re-resolve item_var when root Variable changes."""
                        if updating["flag"]:
                            return
                        assert item_var_path is not None
                        assert resolve_or_create_variable_fn is not None
                        assert set_current_index_fn is not None
                        new_source = resolve_or_create_variable_fn(host, item_var_path, None)
                        if new_source is None:
                            return

                        new_item: Any = None
                        if isinstance(new_source, VarType):
                            new_item = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                        elif isinstance(new_source, (Observable, ObservableProxy)):
                            new_item = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]

                        if new_item is not None:
                            updating["flag"] = True
                            try:
                                idx = find_index_of_item(new_item)
                                if idx >= 0:
                                    set_current_index_fn(idx)
                            finally:
                                updating["flag"] = False

                    root_variable.on_change(on_root_variable_change_combo_item)

        if text_var is not None and set_current_index_fn is not None:

            def on_text_var_change_combo(new_text: str | None) -> None:
                logger.debug(f"[selectedText] on_text_var_change_combo: new_text={new_text!r}")
                if not is_model_valid():
                    logger.debug("[selectedText] model not valid, returning")
                    return
                if updating["flag"]:
                    logger.debug("[selectedText] already updating, returning")
                    return
                updating["flag"] = True
                try:
                    # Update intended_text for when items are added later
                    binding_container["intended_text"] = new_text
                    idx = find_index_by_display_text(new_text)
                    logger.debug(f"[selectedText] find_index_by_display_text({new_text!r}) = {idx}")
                    if idx >= 0:
                        set_current_index_fn(idx)
                        # Remember what we selected for re-selection after model reset
                        binding_container["last_selected_text"] = new_text
                        # Only clear intended_text if this IS the intended text
                        # (When multiple widgets share the same Variable, another widget's
                        # successful selection shouldn't clear OUR intended_text)
                        current_intended = binding_container.get("intended_text")
                        if current_intended == new_text:
                            binding_container.pop("intended_text", None)
                        # Also update index_var if present
                        if index_var is not None:
                            set_index_var_value(idx)
                        # Also update item_var if present
                        set_item_var_value(get_item_at_index(idx), idx)
                    else:
                        logger.debug(f"[selectedText] no match found, intended_text set to {new_text!r}")
                finally:
                    updating["flag"] = False

            text_var.on_change(on_text_var_change_combo)
            logger.debug(f"[selectedText] Connected on_change callback to text_var (widget id={id(widget)})")

            # Also re-sync when model items change (e.g., items loaded after widget created)
            def on_model_rows_inserted() -> None:
                logger.debug("[selectedText] on_model_rows_inserted called")
                if not is_model_valid():
                    logger.debug("[selectedText] model not valid in rowsInserted")
                    return

                # Try intended_text first, then fall back to last_selected_text
                # (When multiple widgets share the same Variable, another widget may have
                # cleared intended_text, but last_selected_text remembers what we wanted)
                intended_text = binding_container.get("intended_text")
                last_selected = binding_container.get("last_selected_text")
                text_to_select = intended_text or last_selected

                logger.debug(f"[selectedText] intended_text={intended_text!r}, last_selected={last_selected!r}")

                if text_to_select is None or text_to_select == "":
                    return

                # Check if we need to re-select (current selection doesn't match)
                current_idx = current_widget_index_fn() if current_widget_index_fn else -1
                current_text = get_display_text_at_index(current_idx) if current_idx >= 0 else None

                if current_text == text_to_select:
                    # Already correctly selected, nothing to do
                    return

                updating["flag"] = True
                try:
                    idx = find_index_by_display_text(text_to_select)
                    logger.debug(f"[selectedText] rowsInserted: find_index_by_display_text({text_to_select!r}) = {idx}")
                    if idx >= 0:
                        set_current_index_fn(idx)
                        # Verify it took
                        actual_idx = current_widget_index_fn() if current_widget_index_fn else -999
                        logger.debug(f"[selectedText] rowsInserted: set index {idx}, widget now shows {actual_idx}")
                        # Update text_var to match (in case auto-selection changed it)
                        set_text_var_value(text_to_select)
                        # Remember what we selected for re-selection if widget resets
                        binding_container["last_selected_text"] = text_to_select
                        # Clear intended_text since we found a match
                        binding_container.pop("intended_text", None)
                finally:
                    updating["flag"] = False

            # Connect to model's rowsInserted and modelReset signals
            # (modelReset fires when the entire list is replaced)
            try:
                model.rowsInserted.connect(on_model_rows_inserted)
                logger.debug("[selectedText] Connected rowsInserted signal")
            except AttributeError:
                logger.debug("[selectedText] Model has no rowsInserted signal")
            try:
                model.modelReset.connect(on_model_rows_inserted)
                logger.debug("[selectedText] Connected modelReset signal")
            except AttributeError:
                logger.debug("[selectedText] Model has no modelReset signal")

            # For nested paths like "workspace?.active_environment_name", subscribe to ROOT
            # Variable changes. When root changes from None to a real object (or vice versa),
            # we need to re-resolve the text_var path and sync the selection.
            if root_variable is not None and text_var_path is not None and resolve_or_create_variable_fn is not None:
                from qtpie.variable import Variable as VarType

                # Track if we've already subscribed to avoid duplicates
                root_subscribed_key = f"text_root_subscribed_{id(widget)}"
                if not binding_container.get(root_subscribed_key, False):
                    binding_container[root_subscribed_key] = True

                    def on_root_variable_change(*_args: Any) -> None:
                        """Re-resolve text_var when root Variable changes (e.g., workspace None→Workspace)."""
                        if updating["flag"]:
                            return

                        # Re-resolve the text path to get the new Observable
                        assert text_var_path is not None  # Checked above
                        assert resolve_or_create_variable_fn is not None  # Checked above
                        new_source = resolve_or_create_variable_fn(host, text_var_path, str)
                        if new_source is None:
                            return

                        # Get the new text value
                        new_text: str | None = None
                        if isinstance(new_source, VarType):
                            new_text = new_source.value  # type: ignore[assignment]
                        elif isinstance(new_source, (Observable, ObservableProxy)):
                            val: Any = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]
                            new_text = str(val) if val is not None else None  # pyright: ignore[reportUnknownArgumentType]

                        logger.debug(f"[selectedText] on_root_variable_change: new_text={new_text!r}")

                        if new_text is not None and new_text != "":
                            # Update intended_text and try to select
                            binding_container["intended_text"] = new_text
                            # Use existing logic from on_text_var_change_combo
                            on_text_var_change_combo(new_text)  # pyright: ignore[reportUnknownArgumentType]
                        else:
                            # Root became None - clear intended_text
                            binding_container["intended_text"] = None
                            binding_container.pop("last_selected_text", None)

                    root_variable.on_change(on_root_variable_change)
                    logger.debug(f"[selectedText] Connected root variable change callback for path={text_var_path}")

        # Widget → Variable binding
        # IMPORTANT: Always connect the handler on first setup, even if item_var is None.
        # This ensures the selection binding handler is connected BEFORE user's signal handlers,
        # so when the signal fires, we update the Variable BEFORE user's handler runs.
        if current_index_changed is not None:

            def on_widget_selection_changed_combo(new_idx: int) -> None:
                logger.debug(f"[selectedText] on_widget_selection_changed_combo: new_idx={new_idx}")
                # Guard: check if model is still valid (not deleted when widget was recreated)
                if not is_model_valid():
                    logger.debug("[selectedText] widget change: model not valid")
                    return
                if updating["flag"]:
                    logger.debug("[selectedText] widget change: already updating, skipping")
                    return

                # Check if selection was unexpectedly reset (e.g., by rowsInserted shifting indices)
                # If we have a "last selected text" and the new index doesn't match it, re-select
                last_selected = binding_container.get("last_selected_text")
                if new_idx == -1 and last_selected is not None and set_current_index_fn is not None:
                    logger.debug(f"[selectedText] widget reset to -1, re-selecting '{last_selected}'")
                    # Try to re-select the item we had selected
                    idx = find_index_by_display_text(last_selected)
                    if idx >= 0:
                        updating["flag"] = True
                        try:
                            set_current_index_fn(idx)
                            logger.debug(f"[selectedText] re-selected index {idx}")
                        finally:
                            updating["flag"] = False
                        return

                # Get current vars from container (may be None on first setup, valid later)
                current_item_var = binding_container["item_var"]
                current_index_var = binding_container.get("index_var")
                current_text_var = binding_container.get("text_var")
                if current_index_var is None and current_item_var is None and current_text_var is None:
                    # No bindings yet, nothing to do
                    return
                updating["flag"] = True
                try:
                    if current_index_var is not None:
                        set_index_var_value(new_idx)
                    set_item_var_value(get_item_at_index(new_idx), new_idx)
                    if current_text_var is not None:
                        display_text = get_display_text_at_index(new_idx)
                        if display_text is not None:
                            set_text_var_value(display_text)
                            # Remember what we selected for re-selection if needed
                            binding_container["last_selected_text"] = display_text
                finally:
                    updating["flag"] = False

            # Only connect if handler wasn't already connected
            if not handler_connected:
                current_index_changed.connect(on_widget_selection_changed_combo)
                binding_container["connected"] = True

    else:
        # QListView/QTableView - use selectionModel
        from qtpy.QtCore import QItemSelectionModel

        selection_model = widget.selectionModel()  # type: ignore[attr-defined]
        if selection_model is None:
            return

        # Store selection model in container - when model changes, selection model changes too
        old_selection_model = binding_container.get("selection_model")
        binding_container["selection_model"] = selection_model

        # If selection model changed, we need to reconnect the handler
        if old_selection_model is not None and old_selection_model is not selection_model:
            handler_connected = False  # Force reconnect to new selection model

        # Helper to get/set item_var value (handles Variable, Observable, and ObservableProxy)
        def get_item_var_value_view() -> Any:
            current_item_var = binding_container["item_var"]
            if current_item_var is None:
                return None
            if binding_container["is_item_observable"]:
                return current_item_var.get()  # pyright: ignore[reportUnknownMemberType]
            if binding_container["is_item_proxy"]:
                return current_item_var.unwrap()  # pyright: ignore[reportUnknownMemberType]
            return current_item_var.value  # pyright: ignore[reportUnknownMemberType]

        def set_item_var_value_view(val: Any, idx: int = -1) -> None:
            """Set the item variable value, using replace_wrapper for complex objects.

            For Variables with ObservableProxy wrappers AND complex object values
            (dataclasses, custom classes), we use replace_wrapper() with the model's
            cached proxy to enable per-item dirty state tracking.

            Variable.replace_wrapper() preserves on_change callbacks by re-registering
            them on the new wrapper.
            """
            from dataclasses import is_dataclass
            from enum import Enum

            current_item_var = binding_container["item_var"]
            if current_item_var is None:
                return
            if binding_container["is_item_observable"]:
                current_item_var.set(val)
            elif binding_container["is_item_proxy"]:
                current_item_var.replace_target(val)
            else:
                proxy = get_proxy_at_index(idx) if idx >= 0 else None
                current_wrapper = getattr(current_item_var, "_wrapper", None)

                is_complex_object = False
                if val is not None:
                    val_type = type(val)  # pyright: ignore[reportUnknownArgumentType,reportUnknownVariableType]
                    is_dataclass_instance = is_dataclass(val) and not isinstance(val, type)
                    is_enum = isinstance(val, Enum)
                    is_builtin = val_type.__module__ == "builtins"
                    has_dict = hasattr(val, "__dict__")
                    is_complex_object = is_dataclass_instance or (has_dict and not is_enum and not is_builtin)

                if proxy is not None and is_complex_object and hasattr(current_item_var, "replace_wrapper") and isinstance(current_wrapper, ObservableProxy):
                    current_item_var.replace_wrapper(proxy)
                else:
                    current_item_var.value = val

        # Helper to set index via selection model
        def set_row_index(row: int) -> None:
            if not is_model_valid():
                return
            current_model = binding_container["model"]
            if row < 0 or row >= current_model.rowCount():
                return
            # Get current selection model from widget (may have changed after model reset)
            current_sel_model = widget.selectionModel()  # type: ignore[attr-defined]
            if current_sel_model is None:
                return
            model_idx = current_model.index(row, 0)
            current_sel_model.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                model_idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )

        # Get current row from selection model
        def get_current_row() -> int:
            current_idx = selection_model.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            if current_idx.isValid():  # pyright: ignore[reportUnknownMemberType]
                return int(current_idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
            return -1

        # Helper to get the embedded widget at a row index (for selectedWidget binding)
        def get_widget_at_row(row: int) -> Any:
            if row < 0:
                return None
            current_model = binding_container["model"]
            if row >= current_model.rowCount():
                return None
            model_idx = current_model.index(row, 0)
            # QAbstractItemView.indexWidget() returns the widget for persistent editors
            return widget.indexWidget(model_idx)  # type: ignore[attr-defined]

        # Initialize from current state
        current_row = get_current_row()

        if index_var is not None:
            initial_idx = get_index_var_value()
            # Variable[int] can have None value if no default provided
            if initial_idx is not None:  # pyright: ignore[reportUnnecessaryComparison]
                set_row_index(initial_idx)
                current_row = initial_idx
            else:
                # Sync Variable to widget's current state
                set_index_var_value(current_row if current_row >= 0 else 0)

        if item_var is not None:
            initial_item = get_item_var_value_view()
            if initial_item is not None:
                # Set widget to match item if index didn't already set it
                if index_var is None:
                    idx = find_index_of_item(initial_item)
                    if idx >= 0:
                        set_row_index(idx)
                        current_row = idx
            else:
                # Sync item Variable to widget's current selection
                effective_row = current_row if current_row >= 0 else 0
                set_item_var_value_view(get_item_at_index(effective_row), effective_row)

        # Initialize widget_var to current selection's widget (read-only binding)
        if widget_var is not None:
            widget_var.value = get_widget_at_row(current_row)

        # text_var (selectedText=) - matches by display text like QComboBox
        # Track if text_var is an Observable (uses .get()/.set()) vs Variable (uses .value)
        binding_container["is_text_observable"] = isinstance(text_var, Observable) if text_var is not None else False

        # Helper to get/set text_var value
        def get_text_var_value_view() -> str | None:
            current_text_var = binding_container.get("text_var")
            if current_text_var is None:
                return None
            if binding_container.get("is_text_observable", False):
                return current_text_var.get()  # type: ignore[no-any-return]
            return current_text_var.value  # type: ignore[no-any-return]

        def set_text_var_value_view(text: str | None) -> None:
            current_text_var = binding_container.get("text_var")
            if current_text_var is None:
                return
            if binding_container.get("is_text_observable", False):
                current_text_var.set(text)
            elif text is not None:
                current_text_var.value = text

        if text_var is not None:
            initial_text = get_text_var_value_view()
            logger.debug(f"[selectedText:ListView] initial_text={initial_text!r}, model rowCount={model.rowCount()}")
            if initial_text:
                # Text is set - find matching item and select it
                idx = find_index_by_display_text(initial_text)
                logger.debug(f"[selectedText:ListView] find_index_by_display_text({initial_text!r}) = {idx}")
                if idx >= 0:
                    # Select if no other binding already set the selection
                    # (index_var or item_var with non-None initial values would have set current_row >= 0)
                    if current_row < 0:
                        set_row_index(idx)
                        current_row = idx
                else:
                    # Text not found yet - store as intended for when items load
                    binding_container["intended_text"] = initial_text
                    logger.debug(f"[selectedText:ListView] items not loaded yet, storing intended_text={initial_text!r}")
            else:
                # No initial text - sync from widget
                effective_row = current_row if current_row >= 0 else 0
                display_text = get_display_text_at_index(effective_row)
                if display_text is not None:
                    set_text_var_value_view(display_text)

        # Variable → Widget binding
        if index_var is not None:

            def on_index_var_change_view(new_idx: int) -> None:
                if not is_model_valid():
                    return
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    set_row_index(new_idx)
                    # Also update item_var if both bindings are present
                    current_item_var = binding_container["item_var"]
                    if current_item_var is not None:
                        set_item_var_value_view(get_item_at_index(new_idx), new_idx)
                finally:
                    updating["flag"] = False

            index_var.on_change(on_index_var_change_view)

            # For nested paths like "workspace?.selected_index", subscribe to ROOT Variable
            if root_variable is not None and index_var_path is not None and resolve_or_create_variable_fn is not None:
                from qtpie.variable import Variable as VarType

                root_subscribed_key = f"index_root_subscribed_{id(widget)}"
                if not binding_container.get(root_subscribed_key, False):
                    binding_container[root_subscribed_key] = True

                    def on_root_variable_change_index(*_args: Any) -> None:
                        """Re-resolve index_var when root Variable changes."""
                        if updating["flag"]:
                            return
                        assert index_var_path is not None
                        assert resolve_or_create_variable_fn is not None
                        new_source = resolve_or_create_variable_fn(host, index_var_path, int)
                        if new_source is None:
                            return

                        new_idx: int | None = None
                        if isinstance(new_source, VarType):
                            new_idx = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                        elif isinstance(new_source, (Observable, ObservableProxy)):
                            val = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]
                            new_idx = val if isinstance(val, int) else None

                        if new_idx is not None and new_idx >= 0:
                            updating["flag"] = True
                            try:
                                set_row_index(new_idx)  # pyright: ignore[reportUnknownArgumentType]
                            finally:
                                updating["flag"] = False

                    root_variable.on_change(on_root_variable_change_index)

        if item_var is not None:

            def on_item_var_change_view(*_args: Any) -> None:
                if not is_model_valid():
                    return
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    new_item = get_item_var_value_view()
                    idx = find_index_of_item(new_item)
                    if idx >= 0:
                        set_row_index(idx)
                        if binding_container["index_var"] is not None:
                            set_index_var_value(idx)
                finally:
                    updating["flag"] = False

            item_var.on_change(on_item_var_change_view)

            # For nested paths like "workspace?.selected_item", subscribe to ROOT Variable
            if root_variable is not None and item_var_path is not None and resolve_or_create_variable_fn is not None:
                from qtpie.variable import Variable as VarType

                root_subscribed_key = f"item_root_subscribed_{id(widget)}"
                if not binding_container.get(root_subscribed_key, False):
                    binding_container[root_subscribed_key] = True

                    def on_root_variable_change_item(*_args: Any) -> None:
                        """Re-resolve item_var when root Variable changes."""
                        if updating["flag"]:
                            return
                        assert item_var_path is not None
                        assert resolve_or_create_variable_fn is not None
                        new_source = resolve_or_create_variable_fn(host, item_var_path, None)
                        if new_source is None:
                            return

                        new_item: Any = None
                        if isinstance(new_source, VarType):
                            new_item = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                        elif isinstance(new_source, (Observable, ObservableProxy)):
                            new_item = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]

                        if new_item is not None:
                            updating["flag"] = True
                            try:
                                idx = find_index_of_item(new_item)
                                if idx >= 0:
                                    set_row_index(idx)
                            finally:
                                updating["flag"] = False

                    root_variable.on_change(on_root_variable_change_item)

        if text_var is not None:

            def on_text_var_change_view(new_text: str) -> None:
                if not is_model_valid():
                    return
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    idx = find_index_by_display_text(new_text)
                    logger.debug(f"[selectedText:ListView] on_text_var_change: find_index_by_display_text({new_text!r}) = {idx}")
                    if idx >= 0:
                        set_row_index(idx)
                        # Remember what we selected for re-selection after modelReset
                        binding_container["last_selected_text"] = new_text
                        # Update other bindings if present
                        if binding_container["index_var"] is not None:
                            set_index_var_value(idx)
                        current_item_var = binding_container["item_var"]
                        if current_item_var is not None:
                            set_item_var_value_view(get_item_at_index(idx), idx)
                        # Only clear intended_text if this IS the intended text
                        # (don't clear if another widget changed the shared text_var)
                        current_intended = binding_container.get("intended_text")
                        if current_intended == new_text:
                            binding_container.pop("intended_text", None)
                    else:
                        # Item not found yet - store as intended for when items load
                        binding_container["intended_text"] = new_text
                        logger.debug(f"[selectedText:ListView] text not found, storing intended_text={new_text!r}")
                finally:
                    updating["flag"] = False

            text_var.on_change(on_text_var_change_view)

            # Connect to model's rowsInserted and modelReset to handle late item loading
            # (modelReset fires when the entire list is replaced via replace() and clears selection!)
            def on_model_rows_inserted_view(*_args: Any) -> None:
                # Check current selection state - modelReset clears selection!
                current_sel_model = widget.selectionModel()  # type: ignore[attr-defined]
                curr_row = -1
                if current_sel_model is not None:
                    curr_idx = current_sel_model.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    curr_row = int(curr_idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]

                if not is_model_valid():
                    return

                # Try intended_text first, then fall back to last_selected_text
                # (modelReset clears selection, so we need to re-select)
                intended_text = binding_container.get("intended_text")
                last_selected = binding_container.get("last_selected_text")
                text_to_select = intended_text or last_selected

                if text_to_select is None:
                    return

                # Check if selection was reset by modelReset or we have pending intended_text
                if curr_row == -1 or intended_text is not None:
                    # Check if the text is now available
                    idx = find_index_by_display_text(text_to_select)
                    if idx >= 0:
                        updating["flag"] = True
                        try:
                            set_row_index(idx)
                            # Update text_var to match (in case auto-selection changed it)
                            set_text_var_value_view(text_to_select)
                            # Remember what we selected for re-selection if widget resets
                            binding_container["last_selected_text"] = text_to_select
                            # Clear intended_text since we found a match
                            binding_container.pop("intended_text", None)
                            # Update other bindings if present
                            if binding_container["index_var"] is not None:
                                set_index_var_value(idx)
                            if binding_container["item_var"] is not None:
                                set_item_var_value_view(get_item_at_index(idx), idx)
                        finally:
                            updating["flag"] = False

            # Connect to both rowsInserted and modelReset
            try:
                model.rowsInserted.connect(on_model_rows_inserted_view)
                logger.debug("[selectedText:ListView] Connected rowsInserted signal")
            except AttributeError:
                logger.debug("[selectedText:ListView] Model has no rowsInserted signal")
            try:
                model.modelReset.connect(on_model_rows_inserted_view)
                logger.debug("[selectedText:ListView] Connected modelReset signal")
            except AttributeError:
                logger.debug("[selectedText:ListView] Model has no modelReset signal")

        # Widget → Variable binding via selection model's currentChanged signal
        # IMPORTANT: Always connect the handler, even if index_var/item_var are None.
        # This ensures the selection binding handler is connected BEFORE user's signal handlers.
        def on_view_selection_changed(current: QModelIndex, _previous: QModelIndex) -> None:
            if not is_model_valid():
                return
            if updating["flag"]:
                return
            # Get current vars from container (may be None on first setup, valid later)
            current_index_var = binding_container["index_var"]
            current_item_var = binding_container["item_var"]
            current_widget_var = binding_container["widget_var"]
            current_text_var = binding_container.get("text_var")
            if current_index_var is None and current_item_var is None and current_widget_var is None and current_text_var is None:
                # No bindings yet, nothing to do
                return
            updating["flag"] = True
            try:
                row = current.row() if current.isValid() else -1
                if current_index_var is not None:
                    set_index_var_value(row)
                if current_item_var is not None:
                    set_item_var_value_view(get_item_at_index(row) if row >= 0 else None, row)
                if current_widget_var is not None:
                    current_widget_var.value = get_widget_at_row(row)
                if current_text_var is not None:
                    display_text = get_display_text_at_index(row)
                    if display_text is not None:
                        set_text_var_value_view(display_text)
            finally:
                updating["flag"] = False

        # Always connect - handler uses container to get current vars
        # Reconnect if selection model changed (happens when model is replaced)
        if not handler_connected:
            selection_model.currentChanged.connect(on_view_selection_changed)  # pyright: ignore[reportUnknownMemberType]
            binding_container["connected"] = True

        # QListView multi-selection bindings (selectedIndexes, selectedItems)
        # indexes_var and items_list_var are already resolved and passed in
        if indexes_var is not None or items_list_var is not None:
            from qtpy.QtCore import QItemSelection

            # Helper to get selected rows from selection model
            def get_selected_rows() -> list[int]:
                selected_indexes = selection_model.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                rows: set[int] = set()
                for idx in selected_indexes:  # pyright: ignore[reportUnknownVariableType]
                    rows.add(idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
                return sorted(rows)

            # Helper to get items at selected rows
            def get_selected_items() -> list[Any]:
                rows = get_selected_rows()
                return [get_item_at_index(row) for row in rows if get_item_at_index(row) is not None]

            # Initialize multi-selection Variables
            if indexes_var is not None:
                initial_indexes = indexes_var.value
                if initial_indexes is None or not initial_indexes:  # pyright: ignore[reportUnnecessaryComparison]
                    indexes_var.value = get_selected_rows()

            if items_list_var is not None:
                initial_items = items_list_var.value
                if initial_items is None or not initial_items:  # pyright: ignore[reportUnnecessaryComparison]
                    items_list_var.value = get_selected_items()

            # Widget → Variable binding via selectionChanged signal (for multi-selection)
            def on_view_multi_selection_changed(_selected: QItemSelection, _deselected: QItemSelection) -> None:
                if not is_model_valid():
                    return
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    if indexes_var is not None:
                        indexes_var.value = get_selected_rows()
                    if items_list_var is not None:
                        items_list_var.value = get_selected_items()
                finally:
                    updating["flag"] = False

            selection_model.selectionChanged.connect(on_view_multi_selection_changed)  # pyright: ignore[reportUnknownMemberType]
            # Store handler for disconnection when bindings are reapplied
            if qtpie_state is not None and hasattr(qtpie_state, "_handlers"):
                qtpie_state._handlers[handler_key] = on_view_multi_selection_changed
