# Phase 5: Data Binding - Implementation Plan

## Overview

Add two-way data binding between Qt widgets and observable models using the `observant` library. Supports nested path binding with optional chaining (`"person.address?.city"`).

## Architecture

```
qtpie/
├── bindings/                  # NEW MODULE
│   ├── __init__.py
│   ├── registry.py            # BindingRegistry + register_binding() + defaults
│   └── bind.py                # bind() function
├── factories/
│   └── make.py                # ADD: bind, bind_prop parameters
└── decorators/
    └── widget.py              # ADD: process bind metadata
```

---

## Step 1: Add `observant` Dependency

**File:** `qtpie/pyproject.toml`

Add `observant` to dependencies:
```toml
[project]
dependencies = [
  "qtpy>=2.4.3",
  "observant>=0.1.5",
]
```

---

## Step 2: Create Binding Registry

**File:** `qtpie/bindings/registry.py`

### Components

1. **BindingAdapter** - dataclass holding getter/setter/signal info for a widget property
2. **BindingRegistry** - singleton storing adapters keyed by (widget_type, property_name)
3. **register_binding()** - function to register new adapters
4. **Default bindings** - auto-registered for common widgets

### Default Widget Bindings

| Widget | Property | Getter | Setter | Signal |
|--------|----------|--------|--------|--------|
| QLineEdit | text | `text()` | `setText()` | `textChanged` |
| QLabel | text | `text()` | `setText()` | (none - one-way) |
| QTextEdit | text | `toPlainText()` | `setPlainText()` | `textChanged` |
| QPlainTextEdit | text | `toPlainText()` | `setPlainText()` | `textChanged` |
| QSpinBox | value | `value()` | `setValue()` | `valueChanged` |
| QDoubleSpinBox | value | `value()` | `setValue()` | `valueChanged` |
| QCheckBox | checked | `isChecked()` | `setChecked()` | `checkStateChanged` |
| QRadioButton | checked | `isChecked()` | `setChecked()` | `toggled` |
| QComboBox | currentText | `currentText()` | `setCurrentText()` | `currentTextChanged` |
| QSlider | value | `value()` | `setValue()` | `valueChanged` |
| QProgressBar | value | `value()` | `setValue()` | (none - one-way) |
| QDial | value | `value()` | `setValue()` | `valueChanged` |

### API

```python
@dataclass
class BindingAdapter(Generic[TWidget, TValue]):
    getter: Callable[[TWidget], TValue] | None = None
    setter: Callable[[TWidget, TValue], None] | None = None
    signal_name: str | None = None

def register_binding(
    widget_type: type[TWidget],
    property_name: str,
    *,
    getter: Callable[[TWidget], TValue] | None = None,
    setter: Callable[[TWidget, TValue], None] | None = None,
    signal: str | None = None,
    default: bool = False,  # Make this the default prop for widget type
) -> None: ...

def get_binding_registry() -> BindingRegistry: ...
```

---

## Step 3: Create bind() Function

**File:** `qtpie/bindings/bind.py`

### Functionality

- Connect an `IObservable` to a widget property
- Two-way sync with lock to prevent infinite loops
- Initial value sync (model → widget)

### API

```python
def bind(
    observable: IObservable[TValue],
    widget: QWidget,
    prop: str | None = None,  # None = use default for widget type
) -> None: ...
```

### Implementation

```python
def bind(observable, widget, prop=None):
    registry = get_binding_registry()

    # Get property name (explicit or default)
    if prop is None:
        prop = registry.get_default_prop(widget)

    adapter = registry.get(widget, prop)
    if adapter is None:
        raise ValueError(f"No binding for {type(widget).__name__}.{prop}")

    lock = False

    def update_model(value):
        nonlocal lock
        if not lock:
            lock = True
            observable.set(value)
            lock = False

    def update_widget(value):
        nonlocal lock
        if not lock and adapter.setter:
            lock = True
            adapter.setter(widget, value)
            lock = False

    # Widget → Model (if signal exists)
    if adapter.signal_name and adapter.getter:
        signal = getattr(widget, adapter.signal_name)
        signal.connect(lambda: update_model(adapter.getter(widget)))

    # Model → Widget
    observable.on_change(update_widget)

    # Initial sync
    update_widget(observable.get())
```

---

## Step 4: Update make() Factory

**File:** `qtpie/factories/make.py`

### New Parameters

```python
BIND_METADATA_KEY = "qtpie_bind"
BIND_PROP_METADATA_KEY = "qtpie_bind_prop"

def make[T](
    class_type: Callable[..., T],
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | None = None,        # NEW: model path like "person.name" or "person?.address?.city"
    bind_prop: str | None = None,   # NEW: explicit widget property (else uses default)
    **kwargs: Any,
) -> T:
```

### Changes

Store `bind` and `bind_prop` in field metadata:

```python
if bind is not None:
    metadata[BIND_METADATA_KEY] = bind
if bind_prop is not None:
    metadata[BIND_PROP_METADATA_KEY] = bind_prop
```

---

## Step 5: Update @widget Decorator

**File:** `qtpie/decorators/widget.py`

### Changes

After creating widgets, process bind metadata:

```python
from qtpie.bindings import bind, get_binding_registry
from qtpie.factories.make import BIND_METADATA_KEY, BIND_PROP_METADATA_KEY

# In new_init, after setting field values:
for f in fields(cls):
    bind_path = f.metadata.get(BIND_METADATA_KEY)
    if bind_path is not None:
        widget_instance = getattr(self, f.name, None)
        if widget_instance is not None:
            # Get the model observable
            model_attr, *nested = bind_path.split(".", 1)
            model = getattr(self, model_attr, None)

            if model is not None:
                # Check if model has ObservableProxy
                proxy = getattr(model, "_proxy", None) or getattr(self, "_model_proxy", None)

                if proxy is not None:
                    # Get observable for the path
                    if nested:
                        observable = proxy.observable_for_path(nested[0])
                    else:
                        observable = proxy.observable(object, model_attr)

                    # Get property name
                    bind_prop = f.metadata.get(BIND_PROP_METADATA_KEY)
                    if bind_prop is None:
                        bind_prop = get_binding_registry().get_default_prop(widget_instance)

                    bind(observable, widget_instance, bind_prop)
```

**Note:** The actual binding setup needs to be deferred until after `setup_bindings()` is called, since the model may be set there.

---

## Step 6: Tests

**File:** `tests/test_qtpie/test_bindings.py`

### Test Cases

1. **Basic binding** - bind QLineEdit.text to observable string
2. **Two-way sync** - widget change updates model, model change updates widget
3. **No infinite loop** - changes don't ping-pong
4. **Default property** - QLineEdit defaults to "text", QSpinBox to "value"
5. **Explicit bind_prop** - override default property
6. **Nested path** - bind to "person.address.city"
7. **Optional chaining** - bind to "person?.address?.city" with None handling
8. **One-way binding** - QLabel (no signal) only updates from model
9. **Multiple bindings** - multiple widgets bound to same model
10. **Custom widget binding** - register binding for custom widget class

### Example Tests

```python
def test_basic_text_binding(qt: QtDriver) -> None:
    """QLineEdit text should bind to observable string."""
    from dataclasses import dataclass, field
    from observant import ObservableProxy

    @dataclass
    class Dog:
        name: str = ""

    @widget()
    class DogEditor(QWidget):
        model: Dog = make(Dog)
        proxy: ObservableProxy[Dog] = field(init=False)
        name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")

        def setup(self) -> None:
            self.proxy = ObservableProxy(self.model, sync=True)

    w = DogEditor()
    qt.track(w)

    # Model → Widget
    w.proxy.observable(str, "name").set("Buddy")
    assert_that(w.name_edit.text()).is_equal_to("Buddy")

    # Widget → Model
    w.name_edit.setText("Max")
    assert_that(w.model.name).is_equal_to("Max")


def test_nested_path_binding(qt: QtDriver) -> None:
    """Should support nested paths like 'proxy.owner.name'."""
    from dataclasses import dataclass, field
    from observant import ObservableProxy

    @dataclass
    class Owner:
        name: str = ""

    @dataclass
    class Dog:
        owner: Owner = field(default_factory=Owner)

    @widget()
    class DogEditor(QWidget):
        model: Dog = make(Dog)
        proxy: ObservableProxy[Dog] = field(init=False)
        owner_edit: QLineEdit = make(QLineEdit, bind="proxy.owner.name")

        def setup(self) -> None:
            self.proxy = ObservableProxy(self.model, sync=True)

    w = DogEditor()
    qt.track(w)

    # Set via nested path
    w.proxy.observable_for_path("owner.name").set("Alice")
    assert_that(w.owner_edit.text()).is_equal_to("Alice")


def test_optional_chaining(qt: QtDriver) -> None:
    """Should handle None in optional paths gracefully."""
    from dataclasses import dataclass, field
    from observant import ObservableProxy

    @dataclass
    class Owner:
        name: str = ""

    @dataclass
    class Dog:
        owner: Owner | None = None

    @widget()
    class DogEditor(QWidget):
        model: Dog = make(Dog)
        proxy: ObservableProxy[Dog] = field(init=False)
        owner_edit: QLineEdit = make(QLineEdit, bind="proxy.owner?.name")

        def setup(self) -> None:
            self.proxy = ObservableProxy(self.model, sync=True)

    w = DogEditor()
    qt.track(w)

    # With None owner, owner_edit should show empty
    assert_that(w.owner_edit.text()).is_equal_to("")

    # Set owner, name should update
    w.model.owner = Owner(name="Alice")
    # Observable will react to parent change...
```

---

## Step 7: Export Public API

**File:** `qtpie/__init__.py`

```python
from qtpie.bindings import bind, register_binding

__all__ = [
    "action", "make", "menu", "widget", "window",
    "bind", "register_binding",  # NEW
]
```

---

## Implementation Order

1. **Create `qtpie/bindings/registry.py`** - BindingRegistry + defaults (~50 lines)
2. **Create `qtpie/bindings/bind.py`** - bind() function (~40 lines)
3. **Create `qtpie/bindings/__init__.py`** - exports
4. **Update `qtpie/factories/make.py`** - add bind/bind_prop params (~10 lines)
5. **Update `qtpie/decorators/widget.py`** - process bind metadata (~30 lines)
6. **Update `qtpie/pyproject.toml`** - add observant dependency
7. **Update `qtpie/__init__.py`** - export new functions
8. **Create `tests/test_qtpie/test_bindings.py`** - comprehensive tests (~200 lines)
9. **Run tests, fix issues**
10. **Run pyright, fix type errors**
11. **Run ruff, fix lint issues**

---

## Design Decisions

1. **Model storage pattern** - Users declare model and proxy explicitly:
   ```python
   model: Dog = field(default_factory=Dog)
   proxy: ObservableProxy[Dog] = field(init=False)
   ```
   ModelWidget[T] mixin will simplify this in Phase 9.

2. **Binding paths** - Bindings reference the proxy field by name:
   ```python
   name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")
   city_edit: QLineEdit = make(QLineEdit, bind="proxy.address?.city")
   ```

3. **Binding lifecycle** - Bindings are set up after `setup()` hook, so user can create proxy there.

4. **Cleanup** - Rely on Qt's automatic signal disconnection for now.

---

## Success Criteria

- [ ] 10+ new tests passing
- [ ] 0 pyright errors
- [ ] 0 ruff errors
- [ ] Basic two-way binding works
- [ ] Nested paths work (`"address.city"`)
- [ ] Optional chaining works (`"address?.city"`)
- [ ] Default bindings for common widgets
- [ ] Custom binding registration works
