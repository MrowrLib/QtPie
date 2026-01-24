# Cross-Class Consistency Patterns

This file documents features that work **consistently across all QtPie class types**: `Widget`, `Window`, `Menu`, and `AppBase`. The framework guarantees these behaviors are uniform.

## Four Base Classes

QtPie has four decorated base classes that share common functionality:

```python
from qtpie import Widget, Window, Menu, AppBase, widget, window, menu, app
```

| Class | Decorator | Purpose |
|-------|-----------|---------|
| `Widget` | `@widget` | Reusable UI components (extends QWidget) |
| `Window` | `@window` | Main windows (extends QMainWindow) |
| `Menu` | `@menu` | Menus with actions (extends QMenu) |
| `AppBase` | `@app` | Application-level state and tray |

---

## Translation Context

All class types automatically set up translation context for `t()` strings.

```python
@widget
class MyWidget(Widget):
    label: QLabel = new(t("Hello"))  # Context = "MyWidget"

@window(title="Test")
class MyWindow(Window):
    label: QLabel = new(t("Hello"))  # Context = "MyWindow"

@menu(text="&File")
class MyMenu(Menu):
    action: QAction = new(t("Save"))  # Context = "MyMenu"
```

---

## Validators

All class types support `add_validator()` for field validation.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

# Check validity
w.is_valid.get()  # bool - reactive Observable
```

The pattern is identical for `Window`, `Menu`, and `AppBase`:

```python
@app(system_tray=False, window=False)
class MyApp(AppBase):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
```

---

## Dirty Tracking Hook

All class types fire `on_dirty_changed()` when state changes from clean to dirty or vice versa.

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        print(f"Dirty state: {is_dirty}")
```

Works identically on `Window`, `Menu`, and `AppBase`.

---

## Validation Hook

All class types fire `on_valid_changed()` when validation state transitions.

```python
@window(title="Test")
class MyWindow(Window):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "req", lambda v: None if v else "Required")

    @override
    def on_valid_changed(self, is_valid: bool) -> None:
        self.save_button.setEnabled(is_valid)
```

---

## QAction Property Bindings

QAction `enabled=` and `visible=` bind reactively to Variables in `Menu` and `AppBase`.

```python
@menu(text="&File")
class FileMenu(Menu):
    _can_save: Variable[bool] = new(False)
    save_action: QAction = new("Save", enabled="_can_save")

    _show_debug: Variable[bool] = new(False)
    debug_action: QAction = new("Debug", visible="_show_debug")
```

```python
@app(system_tray=True, window=False)
class MyApp(AppBase):
    _can_quit: Variable[bool] = new(False)
    quit_action: QAction = new("Quit", enabled="_can_quit")
```

---

## Variable[T, W] with label= in Form Layout

`Variable[T, W]` with `label=` works in form layouts across `Widget`, `Window`, and `AppBase`.

```python
@widget(layout="form")
class MyWidget(Widget):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")

@window(title="Test", layout="form")
class MyWindow(Window):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")

@app(layout="form")
class MyApp(AppBase):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")
```

---

## Signal Expressions

Signal connections support both simple method names and expression syntax with arguments.

### Simple Method Name (no braces)

```python
@menu(text="&File")
class MyMenu(Menu):
    action: QAction = new("Action", triggered="on_action")

    def on_action(self) -> None:
        print("Triggered!")
```

### Expression with Arguments (use braces)

```python
@menu(text="&File")
class MyMenu(Menu):
    action: QAction = new("Action", triggered="{set_value(99)}")

    def set_value(self, val: int) -> None:
        self.result = val
```

Works on `Menu` and `AppBase` with QAction, and on `Widget`/`Window` with other Qt widgets.

---

## Record Types (Generic Parameter)

All class types support generic `[T]` for typed record binding.

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""

# Widget with record - fields auto-bind by name
@widget(record=Person("Alice"))
class PersonWidget(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name

# Window with record
@window(title="Editor", record=Person("Bob"))
class PersonWindow(Window[Person]):
    name: QLineEdit = new()

# Menu with record - use expression binding
@menu(text="&File", record=State(can_save=True))
class FileMenu(Menu[State]):
    save_action: QAction = new("Save", enabled="{record.can_save}")

# App with record
@app(record=Settings("admin"))
class MyApp(AppBase[Settings]):
    username: QLineEdit = new()
```

---

## Summary: Shared Features Across All Types

| Feature | Widget | Window | Menu | AppBase |
|---------|--------|--------|------|---------|
| Translation context | Yes | Yes | Yes | Yes |
| `add_validator()` | Yes | Yes | Yes | Yes |
| `is_valid` Observable | Yes | Yes | Yes | Yes |
| `on_dirty_changed()` | Yes | Yes | Yes | Yes |
| `on_valid_changed()` | Yes | Yes | Yes | Yes |
| `Variable[T]` fields | Yes | Yes | Yes | Yes |
| `Variable[T, W]` with label= | Yes | Yes | N/A | Yes |
| Record type `[T]` | Yes | Yes | Yes | Yes |
| Signal expressions | Yes | Yes | Yes | Yes |
| QAction enabled/visible binding | N/A | N/A | Yes | Yes |
