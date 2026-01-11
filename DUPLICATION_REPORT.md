# QtPie Duplication Report

This document analyzes code duplication across the core QtPie modules to prepare for refactoring.

## Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~1500 | App/AppBase classes for QApplication |
| `menu.py` | ~1005 | Menu class for QMenu |
| `widget.py` | ~1618 | Widget class for QWidget |
| `window.py` | ~719 | Window class for QMainWindow |
| `widget_repeater.py` | ~658 | WidgetRepeater for list bindings |
| `dict_widget_repeater.py` | ~695 | DictWidgetRepeater for dict bindings |
| `set_widget_repeater.py` | ~541 | SetWidgetRepeater for set bindings |
| `action_repeater.py` | ~294 | ActionRepeater for list→QAction bindings |
| `widget_base.py` | ~52 | **STALE** - Minimal mixin, out of date |

---

## Summary of Duplication Categories

### Core Widget/Window/Menu/App Duplication
1. **Config Classes** - 4 different config dataclasses with overlapping fields
2. **Record Descriptors** - 2 nearly identical implementations
3. **`__init_subclass__` Logic** - 4 implementations with same pattern
4. **`_wrap_init_*` Functions** - 4 implementations, each ~50-100 lines
5. **`_create_layout` Functions** - 3 identical implementations
6. **`_add_to_layout` Functions** - 3 nearly identical implementations
7. **`_is_signal` Functions** - 4 identical implementations
8. **Signal Expression Handlers** - 4 nearly identical implementations (~80 lines each)
9. **Dirty/Valid Properties** - 4 implementations with slight differences
10. **Lifecycle Hooks** - 4 implementations of same hooks
11. **`_detect_required_bindings`** - 3 implementations
12. **Binding Application Logic** - 3 implementations with subtle differences

### Repeater Duplication (NEW)
13. **`_is_primitive_type`** - 4 identical implementations across repeaters
14. **`_PLACEHOLDER_RE`** - 4 identical regex patterns
15. **`_HANDLER_SPEC_RE`** - 3 identical regex patterns
16. **`_resolve_nested_property`** - 4 nearly identical implementations
17. **`_create_item_wrapper`** - 4 nearly identical implementations
18. **`_create_widget_for_item`** - 3 nearly identical implementations
19. **`_bind_*` methods** - Complex binding logic duplicated with variations
20. **`_create_signal_handler`** - 3 nearly identical implementations
21. **List-like interface** - `__getitem__`, `__len__`, `__iter__` duplicated

---

## Detailed Analysis

### 1. Config Classes (4 Implementations)

Each module has its own config dataclass with overlapping fields:

#### `_QtPieConfig` (widget.py:58-76)
```python
class _QtPieConfig:
    __slots__ = ("layout", "margins", "fields", "variable_names", "init_wrapped",
                 "record_type", "record_default", "auto_bind", "widget_props",
                 "object_name", "css_classes", "required_bindings")
```

#### `WindowConfig` (window.py:31-50)
```python
@dataclass
class WindowConfig:
    init_wrapped: bool = False
    auto_bind: bool = True
    widget_props: dict[str, Any]
    object_name: str | None = None
    css_classes: list[str]
    fields: dict[str, NewField]
    variable_names: list[str]
    layout: LayoutType = "vertical"
    margins: int | tuple[int, int, int, int] | None = None
    record_type: type[Any] | None = None
    record_default: Any | None = None
    required_bindings: set[str]
```

#### `MenuConfig` (menu.py:118-138)
```python
@dataclass
class MenuConfig:
    init_wrapped: bool = False
    text: str | None = None  # UNIQUE to Menu
    object_name: str | None = None
    css_classes: list[str]
    widget_props: dict[str, Any]
    fields: dict[str, NewField]
    variable_names: list[str]
    required_bindings: set[str]
    record_type: type[Any] | None = None
    record_default: Any | None = None
    item_order: list[str]  # UNIQUE to Menu
```

#### `AppConfig` (app.py:36-72)
```python
@dataclass
class AppConfig:
    init_wrapped: bool = False
    auto_bind: bool = True
    widget_props: dict[str, Any]
    object_name: str | None = None
    css_classes: list[str]
    fields: dict[str, NewField]
    variable_names: list[str]
    layout: LayoutType = "vertical"
    margins: int | tuple[int, int, int, int] | None = None
    record_type: type[Any] | None = None
    record_default: Any | None = None
    required_bindings: set[str]
    # UNIQUE to App:
    window: bool = True
    system_tray: bool = True
    show: bool = True
    minimize_to_tray: bool = True
    icon, window_icon, tray_icon: ...
    is_qapplication: bool = False
```

**Common Fields (present in ALL):**
- `init_wrapped: bool`
- `object_name: str | None`
- `css_classes: list[str]`
- `widget_props: dict[str, Any]`
- `fields: dict[str, NewField]`
- `variable_names: list[str]`
- `record_type: type[Any] | None`
- `record_default: Any | None`
- `required_bindings: set[str]`

**Inconsistencies:**
- `_QtPieConfig` uses `__slots__` while others use `@dataclass`
- Menu has no `auto_bind` field (always auto-binds?)
- Menu/Widget don't have layout-related fields used consistently

---

### 2. Record Descriptors (2 Implementations)

#### `_RecordDescriptor` (widget.py:78-135)
Used by Widget and Window (imported from widget.py).

#### `_MenuRecordDescriptor` (menu.py:67-111)
Nearly identical to `_RecordDescriptor` but with:
- Different type parameter naming style
- Uses `QtPieState` differently

**Differences:**
| Aspect | Widget `_RecordDescriptor` | Menu `_MenuRecordDescriptor` |
|--------|---------------------------|------------------------------|
| State init | `obj._qtpie = QtPieState(obj)` | Same |
| Wrapper creation | Uses `_create_observable_for_type` | Uses `ObservableProxy` directly |
| Error handling | `ValueError` -> fallback | `TypeError` -> fallback |
| Dirty subscription | `_subscribe_record_to_widget_dirty/valid` | None |

**This is a bug waiting to happen** - Menu's record doesn't participate in dirty/valid aggregation!

---

### 3. `__init_subclass__` Logic (4 Implementations)

All four modules have very similar `__init_subclass__` implementations:

```python
# Pattern repeated in Widget, Window, Menu, AppBase:
def __init_subclass__(cls, **kwargs: Any) -> None:
    super().__init_subclass__(**kwargs)
    cls._qtpie_config = Config()  # Different Config class

    # Extract T from Class[T]
    for base in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(base)
        if origin is <ThisClass>:
            args = get_args(base)
            if args:
                cls._qtpie_config.record_type = args[0]
            break

    # Check explicit record
    has_explicit_record = "record" in cls.__dict__

    # Collect fields
    _collect_fields(cls)

    # Detect required bindings
    _detect_required_bindings(cls)

    # Apply new_fields
    new_fields(cls)

    # Collect variable names
    for name, value in list(cls.__dict__.items()):
        if isinstance(value, _VariableDescriptor):
            cls._qtpie_config.variable_names.append(name)

    # Create record descriptor
    if cls._qtpie_config.record_type is not None and not has_explicit_record:
        cls.record = _RecordDescriptor(cls._qtpie_config.record_type)
```

**Subtle Differences:**
- `Widget`: Collects fields BEFORE new_fields
- `Window`: Collects fields BEFORE new_fields
- `Menu`: Collects fields BEFORE, has `item_order` tracking
- `AppBase`: Collects fields BEFORE, checks `issubclass(cls, QApplication)`

---

### 4. `_wrap_init_*` Functions (4 Implementations)

Each module wraps `__init__` to set up declarative features:

| Function | Location | Lines |
|----------|----------|-------|
| `_wrap_init_for_layout` | widget.py:457-576 | ~120 |
| `_wrap_init_for_window` | window.py:386-555 | ~170 |
| `_wrap_init_for_menu` | menu.py:396-545 | ~150 |
| `_wrap_init_for_app` | app.py:667-761 | ~95 |

**Common Pattern in All:**
1. Check if already wrapped (`config.init_wrapped`)
2. Save original `__init__`
3. Create `wrapped_init` that:
   - Sets translation context
   - Calls original `__init__`
   - Creates list widget fields
   - Applies widget props
   - Sets objectName
   - Applies CSS classes
   - Connects signals
   - Sets record default
   - Calls `__setup__`
   - Applies bindings
   - Enables dirty/valid hooks
4. Replace `cls.__init__`
5. Set `config.init_wrapped = True`

**Key Differences:**
- Widget: Has `_validate_layout_params`, does NOT call shared binding functions
- Window: Uses shared `apply_auto_bindings`, `apply_property_bindings` from `bindings/apply.py`
- Menu: Has item order processing, action property bindings
- App: Creates auto-window, system tray, uses `QtPieStateBase`

---

### 5. `_create_layout` Functions (3 IDENTICAL Implementations)

```python
def _create_layout(layout_type: LayoutType) -> QLayout | None:
    if layout_type == "vertical":
        return QVBoxLayout()
    elif layout_type == "horizontal":
        return QHBoxLayout()
    elif layout_type == "form":
        return QFormLayout()
    elif layout_type == "grid":
        return QGridLayout()
    return None
```

**Locations:**
- `widget.py:601-611`
- `window.py:657-667`
- `app.py:983-993` (named `_create_layout_for_app`)

**Status:** Pure duplication - extract to shared module.

---

### 6. `_add_to_layout` Functions (3 Nearly Identical Implementations)

**Locations:**
- `widget.py:631-680` - Full implementation with Translatable support
- `window.py:670-718` - Copy of widget.py version
- `app.py:996-1026` - Simpler version, no Translatable support

**Differences:**
- App version lacks Translatable/retranslation support
- Widget/Window versions are identical

---

### 7. `_is_signal` Functions (4 IDENTICAL Implementations)

```python
def _is_signal(obj: object) -> bool:
    """Check if obj is a Qt Signal (bound signal instance)."""
    type_name = type(obj).__name__
    return type_name in ("SignalInstance", "pyqtBoundSignal")
```

**Locations:**
- `widget.py:1220-1227`
- `window.py:558-561`
- `menu.py:29-32`
- `app.py:764-767`

**Status:** Pure duplication - extract to shared module.

---

### 8. Signal Expression Handlers (4 Nearly Identical Implementations)

| Function | Location | Lines |
|----------|----------|-------|
| `_create_signal_expression_handler` | widget.py:1279-1366 | ~87 |
| `_create_window_signal_expression_handler` | window.py:564-653 | ~89 |
| `_create_menu_signal_expression_handler` | menu.py:605-693 | ~88 |
| `_create_app_signal_expression_handler` | app.py:770-859 | ~89 |

**All do the same thing:**
1. Parse expression with `_parse_format_fields`
2. Check for `#args`, `#self`/`#widget`/`#menu`/`#app` placeholders
3. Replace placeholders for AST extraction
4. Extract variable names with `_extract_ast_names`
5. Create handler closure that:
   - Builds context with variables
   - Wraps signals as `.emit`
   - Replaces placeholders in expression
   - Evaluates with `eval()`

**Differences (minor):**
- Different placeholder names (`#widget` vs `#menu` vs `#app` vs `#self`)
- Widget uses `widget_ref`, Window uses `window_ref`, Menu uses `menu_ref`, App uses `app_ref`

**This should be one parameterized function!**

---

### 9. Dirty/Valid Properties (4 Implementations with Differences)

#### Widget (widget.py:229-278)
```python
@property
def is_dirty(self) -> Observable[bool]:
    if not hasattr(self, "_qtpie"):
        self._qtpie = QtPieState(self)
    return self._qtpie.widget_is_dirty

@property
def is_valid(self) -> Observable[bool]:
    if not hasattr(self, "_qtpie"):
        self._qtpie = QtPieState(self)
    return self._qtpie.widget_is_valid
```

#### Window (window.py:182-231)
Same as Widget.

#### Menu (menu.py:229-274)
Same as Widget.

#### AppBase (app.py:252-318)
```python
@property
def is_dirty(self) -> Observable[bool]:
    state = getattr(self, "_qtpie_state", None)  # Different attribute name!
    if state is not None:
        return state.is_dirty  # Different property name!
    return Observable[bool](False, dirty_tracking=False, validation=False)
```

**INCONSISTENCY:** AppBase uses `_qtpie_state` and `state.is_dirty`, while Widget/Window/Menu use `_qtpie` and `_qtpie.widget_is_dirty`.

---

### 10. Lifecycle Hooks (4 Implementations)

All four classes define:
```python
def on_dirty_changed(self, is_dirty: bool) -> None: pass
def on_valid_changed(self, is_valid: bool) -> None: pass
```

Widget and Window also have:
```python
async def on_close(self) -> None: pass
```

AppBase has:
```python
def on_system_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None: pass
```

---

### 11. `_detect_required_bindings` Functions (3 Implementations)

| Function | Location |
|----------|----------|
| `_detect_required_bindings` | widget.py:1583-1617 |
| `_detect_required_bindings_for_window` | window.py:243-277 |
| `_detect_required_bindings_for_menu` | menu.py:304-329 |

**All are IDENTICAL** except for the class type parameter in the signature.

---

### 12. Expression Binding Functions (3 Implementations)

| Function | Location | Lines |
|----------|----------|-------|
| `_create_expression_binding` | widget.py:1432-1550 | ~118 |
| `_create_menu_expression_binding` | menu.py:783-955 | ~172 |
| `_create_expression_binding_for_app` | app.py:1375-1470 | ~95 |

**Differences:**
- Menu version has special `#parent` placeholder handling
- App version is slightly simpler
- Widget version is the "standard" implementation

---

### 13. `_resolve_icon` Function (2 Implementations)

| Location | app.py:75-90 | widget.py:32-55 |
|----------|--------------|-----------------|
| Signature | Same | Same |
| Implementation | Same | Same + extra docstring |

Window imports from widget.py. App has its own copy.

---

## Repeater Classes Analysis

The four repeater classes have **massive duplication** with subtle differences that could lead to bugs.

### Files Compared

| File | Collection | Widget Type | Placeholders |
|------|------------|-------------|--------------|
| `widget_repeater.py` | `ObservableList[T]` | `QWidget` | `#self`, `#index`, `{property}` |
| `dict_widget_repeater.py` | `ObservableDict[K,V]` | `QWidget` | `#key`, `#value`, `#self`, `{property}` |
| `set_widget_repeater.py` | `ObservableSet[T]` | `QWidget` | `#self`, `{property}` (NO `#index`!) |
| `action_repeater.py` | `ObservableList[T]` | `QAction` | `#self`, `#index`, `{property}` |

### Identical Code Across All 4 Repeaters

#### `_is_primitive_type` (4x duplicated)
```python
def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))
```

#### `_PLACEHOLDER_RE` (4x duplicated)
```python
_PLACEHOLDER_RE = re.compile(r"\{(#?\w+(?:\.\w+)*)\}")
```

#### `_resolve_nested_property` / `_resolve_property` (4x duplicated, ~20 lines each)
All do the same thing - resolve dotted paths like `breed.name` on objects.

**Differences:**
- `action_repeater.py` names it `_resolve_property`
- Minor pyright ignore comment variations

### Similar But Different Code

#### `_create_item_wrapper` / `_create_key_wrapper` / `_create_value_wrapper`

| Repeater | Method Name | Returns |
|----------|-------------|---------|
| WidgetRepeater | `_create_item_wrapper(item)` | `Observable[T]` or `ObservableProxy[T]` |
| DictWidgetRepeater | `_create_key_wrapper(key)` + `_create_value_wrapper(value)` | Same |
| SetWidgetRepeater | `_create_item_wrapper(item)` | Same |
| ActionRepeater | `_create_item_wrapper(item)` | Same |

**All implementations are IDENTICAL** - just checking `_is_primitive` and returning Observable vs ObservableProxy.

#### `_create_widget_for_item` / `_create_widget_for_entry` (3 widgets, 1 action)

| Repeater | Method | Creates |
|----------|--------|---------|
| WidgetRepeater | `_create_widget_for_item` | `self._widget_type(...)` + objectName + CSS classes + widget_props |
| DictWidgetRepeater | `_create_widget_for_entry` | Same |
| SetWidgetRepeater | `_create_widget_for_item` | Same |
| ActionRepeater | `_create_action_for_item` | `QAction(text, menu)` + triggered handler |

**Widget repeaters are IDENTICAL** (~20 lines each). ActionRepeater is different (QAction-specific).

#### `_create_signal_handler` (3 implementations)

| Repeater | Placeholders Supported |
|----------|----------------------|
| WidgetRepeater | `#value`, `#widget`, `#index`, `#args` |
| DictWidgetRepeater | `#value`, `#key`, `#widget`, `#args` |
| SetWidgetRepeater | `#value`, `#widget`, `#args` (NO `#index`!) |

**~50 lines each, 90% identical.** Should be one function with placeholder config.

### Binding Logic Duplication

The binding methods are the most complex duplication:

| Method Pattern | WidgetRepeater | DictRepeater | SetRepeater | ActionRepeater |
|----------------|----------------|--------------|-------------|----------------|
| `_bind_widget_to_item` | ✓ | ✓ (`_bind_widget_to_entry`) | ✓ | N/A |
| `_bind_callable_format` | ✓ | ✓ | ✓ | N/A (inline) |
| `_bind_computed_format` | ✓ | ✓ | ✓ | N/A |
| `_setup_primitive_sync` | ✓ | ✓ (`_setup_value_sync`) | ✗ (missing!) | N/A |

**Bug Found:** `SetWidgetRepeater` is **missing** `_setup_primitive_sync`!
- For `list[int]`: editing widget updates list ✓
- For `set[int]`: editing widget does NOT update set ✗

This is a real bug caused by copy-paste duplication without full implementation.

### Feature Matrix

| Feature | WidgetRepeater | DictRepeater | SetRepeater | ActionRepeater |
|---------|----------------|--------------|-------------|----------------|
| `sort=` parameter | ✓ | ✓ | ✓ | ✗ |
| Two-way binding | ✓ | ✓ | ✗ (BUG) | ✗ |
| `{#index}` | ✓ | ✗ | ✗ | ✓ |
| `{#key}` | ✗ | ✓ | ✗ | ✗ |
| `{#value}` | ✓ (`#self`) | ✓ | ✓ (`#self`) | ✓ (`#self`) |
| Signal connections | ✓ | ✓ | ✓ | Only `triggered` |
| CSS classes | ✓ | ✓ | ✓ | ✗ |
| objectName | ✓ | ✓ | ✓ | ✗ |
| widget_props | ✓ | ✓ | ✓ | ✗ |
| Callable formatter | ✓ | ✓ | ✓ | ✓ |

### Inconsistencies

1. **SetWidgetRepeater missing two-way sync** - primitives don't sync back to set
2. **ActionRepeater lacks many features** - no sort, CSS classes, objectName, widget_props
3. **Different default bind expressions:**
   - WidgetRepeater: `"{#self}"`
   - DictWidgetRepeater: `"{#key} = {#value}"`
   - SetWidgetRepeater: `"{#self}"`
   - ActionRepeater: `"{#self}"`

4. **Sorting implementation differs:**
   - WidgetRepeater: Maintains `_layout_indices` list, rebuilds layout order
   - DictWidgetRepeater: Maintains `_layout_order` list of keys
   - SetWidgetRepeater: Uses `_find_insert_position` for insertion sort
   - ActionRepeater: No sorting at all

---

## `widget_base.py` Analysis

**Status: STALE / OUT OF DATE**

This file is only 52 lines and provides a `WidgetBase` mixin. It's missing:
- Config class
- Record support
- Dirty/valid tracking
- Validation
- Lifecycle hooks
- Property bindings
- CSS classes
- objectName
- Most features that Widget/Window/Menu have

**It only does:**
1. `__init_subclass__` calls `new_fields(cls)`
2. Wraps `__init__` to call `__setup__`

This should either be removed or updated to match Widget's feature set.

---

## Inconsistencies That Could Cause Bugs

### 1. State Attribute Naming
- Widget/Window/Menu: `self._qtpie` → `QtPieState`
- AppBase: `self._qtpie_state` → `QtPieStateBase`

### 2. Dirty Observable Access
- Widget/Window/Menu: `self._qtpie.widget_is_dirty`
- AppBase: `self._qtpie_state.is_dirty`

### 3. Menu Record Missing Dirty Subscription
Menu's `_MenuRecordDescriptor` doesn't call:
```python
state._subscribe_record_to_widget_dirty()
state._subscribe_record_to_widget_valid()
```
This means Menu[T].record changes won't update `is_dirty`/`is_valid`.

### 4. Missing `_validate_layout_params` in Window
Widget validates that form layouts have labels and grid layouts have positions.
Window does NOT validate - could silently fail.

### 5. App Binding Logic Different
- Widget: Uses inline `_apply_auto_bindings` function
- Window: Uses shared `apply_auto_bindings` from `bindings/apply.py`
- App: Uses inline `_apply_app_bindings` function

Different implementations could have different behaviors.

---

## Refactoring Recommendations

### Phase 1: Extract Pure Utilities
1. `_is_signal()` → `lib/qtpie/utils/signals.py`
2. `_create_layout()` → `lib/qtpie/utils/layouts.py`
3. `_resolve_icon()` → `lib/qtpie/utils/icons.py`

### Phase 2: Unify Config Classes
Create a base config class:
```python
@dataclass
class QtPieBaseConfig:
    init_wrapped: bool = False
    object_name: str | None = None
    css_classes: list[str]
    widget_props: dict[str, Any]
    fields: dict[str, NewField]
    variable_names: list[str]
    record_type: type[Any] | None = None
    record_default: Any | None = None
    required_bindings: set[str]
```

Then extend for specific needs:
```python
@dataclass
class WidgetConfig(QtPieBaseConfig):
    layout: LayoutType = "vertical"
    margins: int | tuple[int, int, int, int] | None = None
    auto_bind: bool = True

@dataclass
class MenuConfig(QtPieBaseConfig):
    text: str | None = None
    item_order: list[str]
```

### Phase 3: Unify Record Descriptors
Extract to `lib/qtpie/descriptors/record.py`:
```python
class RecordDescriptor[T]:
    def __init__(self, record_type: type[T], state_class: type = QtPieState): ...
```

### Phase 4: Create Shared `__init_subclass__` Helper
```python
def setup_qtpie_subclass(
    cls: type,
    config_class: type,
    base_class: type,
    record_descriptor_class: type,
) -> None:
    # Common subclass setup logic
```

### Phase 5: Unify Signal Expression Handlers
```python
def create_signal_expression_handler(
    context_obj: Any,
    expression: str,
    self_placeholder: str = "#self",  # or "#widget", "#menu", "#app"
) -> Callable[..., Any]:
```

### Phase 6: Unify Binding Application
Move everything to `bindings/apply.py`:
- `apply_auto_bindings`
- `apply_property_bindings`
- `apply_reactive_widget_props`
- `create_expression_binding`

All modules should use these shared functions.

### Phase 7: Fix WidgetBase or Remove
Either:
- Update to use shared infrastructure
- Remove and document that Widget/Window/Menu should be used

---

## Test Impact

The existing 1282 tests should serve as a regression suite. Run after each refactoring step:
```bash
uv run pytest tests/ -v
uv run pyright lib/qtpie/ tests/qtpie/
uv run ruff check lib/qtpie/ tests/
```

---

## Priority Order

1. **HIGH**: Fix Menu record dirty subscription bug
2. **HIGH**: Unify `_is_signal`, `_create_layout` (pure functions, zero risk)
3. **MEDIUM**: Unify signal expression handlers (one parameterized function)
4. **MEDIUM**: Unify config classes (base class + extensions)
5. **LOW**: Unify `__init_subclass__` logic (more complex, higher risk)
6. **LOW**: Unify `_wrap_init_*` functions (very complex, highest risk)
