# QtPie

**Declarative UI framework for Qt/PySide6**

QtPie brings React/Vue-style declarative patterns to desktop app development. Define *what* your UI should look like, not *how* to build it.

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, Variable, new, widget, entrypoint

@entrypoint
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("Increment", clicked="on_click")

    def on_click(self) -> None:
        self._count += 1
```

Run `python counter.py` and you have a working app with automatic layout, reactive data binding, and declarative signal connections.

## Installation

=== "uv"

    ```bash
    uv add qtpie
    ```

=== "pip"

    ```bash
    pip install qtpie
    ```

=== "poetry"

    ```bash
    poetry add qtpie
    ```

---

## Core Concepts

### Declarative Widgets

Define widgets as classes with type-annotated fields. No `__init__` boilerplate, no manual layout code.

```python
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton
from qtpie import Widget, new, widget

@widget
class LoginForm(Widget):
    _title: QLabel = new("Sign In")
    _username: QLineEdit = new(placeholderText="Username")
    _password: QLineEdit = new(placeholderText="Password", echoMode=QLineEdit.EchoMode.Password)
    _submit: QPushButton = new("Login", clicked="on_login")

    def on_login(self) -> None:
        print(f"Logging in as {self._username.text()}")
```

Fields are automatically added to a vertical layout. Use `@widget(layout="horizontal")` or `@widget(layout="form")` for alternatives.

[Learn more about Widgets](basics/widgets.md)

---

### Reactive State with Variables

`Variable[T]` holds reactive state. When it changes, bound widgets update automatically.

```python
from qtpie import Variable

@widget
class TemperatureConverter(Widget):
    _celsius: Variable[float] = new(0.0)

    _input: QLineEdit = new(bind="_celsius")
    _output: QLabel = new(bind="{_celsius * 9/5 + 32:.1f}°F")
```

Type the temperature in Celsius, see Fahrenheit update instantly.

[Learn more about Variables](state/variables.md)

---

### Data Binding

The `bind=` parameter connects widgets to data with format expressions:

```python
@widget
class Profile(Widget):
    _name: Variable[str] = new("Alice")
    _level: Variable[int] = new(42)

    # Simple binding
    _name_input: QLineEdit = new(bind="_name")

    # Format expression with Python code
    _status: QLabel = new(bind="{_name.upper()} - Level {_level}")

    # Conditional visibility
    _vip_badge: QLabel = new("VIP", visible="{_level >= 50}")
```

Expressions support method calls, math, string formatting, and more.

[Learn more about Bindings](state/bindings.md) | [Format Expressions](state/format-expressions.md)

---

### Record Types for Forms

Bind dataclasses directly to widgets with `Widget[T]`. Fields matching record properties auto-bind.

```python
from dataclasses import dataclass

@dataclass
class Contact:
    name: str = ""
    email: str = ""
    phone: str = ""

@widget(record=Contact())
class ContactForm(Widget[Contact]):
    name: QLineEdit = new(label="Name:")      # Auto-binds to record.name
    email: QLineEdit = new(label="Email:")    # Auto-binds to record.email
    phone: QLineEdit = new(label="Phone:")    # Auto-binds to record.phone

    _save: QPushButton = new("Save", clicked="on_save")

    def on_save(self) -> None:
        contact = self.record  # Access the bound dataclass
        print(f"Saving {contact.name} <{contact.email}>")
```

[Learn more about Records](data/records.md)

---

### Validation & Dirty Tracking

Built-in support for form validation and change detection:

```python
@widget(record=User())
class UserForm(Widget[User]):
    name: QLineEdit = new(validate=lambda v: None if v else "Name required")
    email: QLineEdit = new(validate=lambda v: None if "@" in v else "Invalid email")

    _errors: QLabel = new(bind="{', '.join(validation_error_messages)}")
    _save: QPushButton = new("Save", enabled="{is_valid and view_model.is_dirty}")
```

The save button only enables when the form is valid AND has unsaved changes.

[Validation](data/validation.md) | [Dirty Tracking](data/dirty-tracking.md)

---

### Dynamic Lists with Repeaters

Bind lists and dicts to create dynamic widget collections:

```python
@widget
class TodoApp(Widget):
    _todos: Variable[list[str]] = new(["Buy groceries", "Walk dog"])

    # One QLabel per item, auto-synced
    _items: list[QLabel] = new(bind="_todos", format="- {#value}")

    _new_todo: QLineEdit = new(placeholderText="New todo...")
    _add: QPushButton = new("Add", clicked="on_add")

    def on_add(self) -> None:
        self._todos.append(self._new_todo.text())
        self._new_todo.clear()
```

Add items to the list, widgets appear automatically.

[Learn more about Repeaters](data/repeaters.md)

---

### Parent-Child Communication

Pass state down to child widgets via Variable bindings:

```python
@widget
class CounterDisplay(Widget):
    count: Variable[int]  # Required from parent
    _label: QLabel = new(bind="Count: {count}")

@widget
class App(Widget):
    _my_count: Variable[int] = new(0)

    # State flows down to child
    _display: CounterDisplay = new(count="_my_count")
    _increment: QPushButton = new("+", clicked="on_increment")

    def on_increment(self) -> None:
        self._my_count += 1  # Display updates automatically
```

[Learn more about Widget Bindings](state/widget-bindings.md)

---

### Windows & Menus

Build full applications with `Window` and declarative menus:

```python
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from qtpie import Window, window, menu

@menu("&File")
class FileMenu(QMenu):
    new: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open: QAction = new("&Open", shortcut="Ctrl+O", triggered="on_open")
    save: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")

    def on_new(self) -> None: ...
    def on_open(self) -> None: ...
    def on_save(self) -> None: ...

@window(title="My Editor", size=(800, 600))
class EditorWindow(Window):
    _file_menu: FileMenu = new()  # Auto-added to menu bar
    _content: QTextEdit = new()
```

[Learn more about Windows & Menus](guides/windows-menus.md)

---

### Styling

Dark mode, SCSS compilation, and hot-reload for rapid development:

```python
@entrypoint(
    dark_mode=True,
    stylesheet="styles/app.scss",
    watch_stylesheet=True  # Hot-reload on save
)
@widget
class MyApp(Widget):
    _title: QLabel = new("Styled App", name="main-title", classes=["header"])
```

```scss
// styles/app.scss
$primary: #0078d4;

#main-title {
    font-size: 24px;
    color: $primary;
}

.header {
    font-weight: bold;
}
```

[Learn more about Styling](guides/styling.md)

---

### Translations

Built-in i18n with YAML-based translation files:

```python
from qtpie import t, set_language

@entrypoint(translations="i18n/messages.yml", language="en")
@widget
class MyApp(Widget):
    _greeting: QLabel = new(t("Hello"))
    _lang_btn: QPushButton = new(t("Switch Language"), clicked="toggle_lang")

    def toggle_lang(self) -> None:
        set_language("fr")  # UI retranslates automatically
```

```yaml
# i18n/messages.yml
:global:
    Hello:
        en: Hello
        fr: Bonjour
    Switch Language:
        en: Switch Language
        fr: Changer de langue
```

[Learn more about Translations](guides/translations.md)

---

## Feature Overview

| Feature | Description |
|---------|-------------|
| **Declarative Widgets** | Type-annotated fields, automatic layouts |
| **Reactive State** | `Variable[T]` with automatic UI updates |
| **Data Binding** | `bind=` with format expressions and Python code |
| **Record Types** | `Widget[T]` for dataclass-bound forms |
| **Validation** | Per-field validators with error aggregation |
| **Dirty Tracking** | Automatic change detection |
| **Repeaters** | Dynamic widget lists from data |
| **Property Bindings** | Reactive `visible=`, `enabled=` |
| **Windows & Menus** | Full application structure |
| **Styling** | Dark mode, SCSS, hot-reload |
| **Translations** | YAML-based i18n system |
| **Type Safety** | Full pyright strict compatibility |

---

## Next Steps

<div class="grid cards" markdown>

-   :material-puzzle:{ .lg .middle } **Widgets**

    ---

    Learn the fundamentals of declarative widget definition

    [:octicons-arrow-right-24: Get started](basics/widgets.md)

-   :material-refresh:{ .lg .middle } **Variables**

    ---

    Understand reactive state and data flow

    [:octicons-arrow-right-24: Learn more](state/variables.md)

-   :material-application:{ .lg .middle } **App & Entry Points**

    ---

    Build complete applications with @entrypoint and @app

    [:octicons-arrow-right-24: Build apps](guides/app.md)

-   :material-compare:{ .lg .middle } **Why QtPie?**

    ---

    See the before/after comparison with plain Qt

    [:octicons-arrow-right-24: Compare](why-qtpie.md)

</div>
