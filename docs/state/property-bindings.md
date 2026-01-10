# Property Bindings

Property bindings reactively control widget state like visibility and enabled status based on Variables.

## visible= and enabled=

```python
from qtpie import Widget, Variable, new, widget

@widget
class MyWidget(Widget):
    _show_panel: Variable[bool] = new(True)
    _can_submit: Variable[bool] = new(False)

    _panel: QLabel = new("Panel content", visible="_show_panel")
    _submit: QPushButton = new("Submit", enabled="_can_submit")
```

When the Variable changes, the widget's property updates automatically.

## Simple Variable Binding

Reference a Variable by field name:

```python
@widget
class TogglePanel(Widget):
    _is_visible: Variable[bool] = new(True)
    _panel: QWidget = new(visible="_is_visible")

    _toggle: QPushButton = new("Toggle", clicked="toggle")

    def toggle(self) -> None:
        self._is_visible = not self._is_visible.value
```

## Expression Bindings

Use `{...}` for Python expressions that evaluate to boolean:

```python
@widget
class FormWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    # String length check
    _submit: QPushButton = new(
        "Submit",
        enabled="{len(_name) > 0}"
    )

    # Numeric comparison
    _warning: QLabel = new(
        "Low count!",
        visible="{_count < 5}"
    )
```

### Boolean Logic

Combine conditions with `and`, `or`, `not`:

```python
@widget
class Dashboard(Widget):
    _logged_in: Variable[bool] = new(False)
    _is_admin: Variable[bool] = new(False)

    # Both must be true
    _admin_panel: QWidget = new(
        visible="{_logged_in and _is_admin}"
    )

    # Either condition
    _guest_notice: QLabel = new(
        "Welcome!",
        visible="{not _logged_in or not _is_admin}"
    )
```

## Multiple Properties

Apply both `visible=` and `enabled=` to the same widget:

```python
@widget
class MultiPropWidget(Widget):
    _show: Variable[bool] = new(True)
    _allow: Variable[bool] = new(True)

    _button: QPushButton = new(
        "Action",
        visible="_show",
        enabled="_allow"
    )
```

## Reactive Decorator Properties

Decorator keyword arguments can also be reactive:

```python
@widget(windowTitle="{_title}")
class DynamicTitle(Widget):
    _title: Variable[str] = new("My App")

    def update_title(self, new_title: str) -> None:
        self._title = new_title  # Window title updates!
```

### Multi-Variable Expressions

```python
@widget(windowTitle="{_app_name} - {_filename}")
class Editor(Widget):
    _app_name: Variable[str] = new("Editor")
    _filename: Variable[str] = new("untitled.txt")

    def open_file(self, path: str) -> None:
        self._filename = path  # Title becomes "Editor - path"
```

### Conditional Decorator Properties

```python
@widget(windowTitle="{_filename}{_has_changes and ' *' or ''}")
class DocumentEditor(Widget):
    _filename: Variable[str] = new("untitled.txt")
    _has_changes: Variable[bool] = new(False)
    # Shows "untitled.txt" or "untitled.txt *" when dirty
```

## Common Patterns

### Login Form

```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")
    _is_loading: Variable[bool] = new(False)

    username: QLineEdit = new(placeholderText="Username")
    password: QLineEdit = new(
        placeholderText="Password",
        echoMode=QLineEdit.EchoMode.Password
    )

    # Enable only when both fields filled and not loading
    _login_btn: QPushButton = new(
        "Login",
        enabled="{len(_username) > 0 and len(_password) > 0 and not _is_loading}",
        clicked="do_login"
    )

    # Show spinner during loading
    _spinner: QLabel = new("Loading...", visible="_is_loading")

    def do_login(self) -> None:
        self._is_loading = True
        # ... async login logic
```

### Conditional Settings Panel

```python
@widget
class SettingsPanel(Widget):
    _show_advanced: Variable[bool] = new(False)

    # Toggle button
    _toggle: QPushButton = new(
        "Show Advanced",
        clicked="toggle_advanced"
    )

    # Basic settings always visible
    _basic: QWidget = new()

    # Advanced settings hidden by default
    _advanced: QWidget = new(visible="_show_advanced")

    def toggle_advanced(self) -> None:
        self._show_advanced = not self._show_advanced.value
```

### Error Messages

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _name_error: QLabel = new(
        "Name is required",
        visible="{len(_name) == 0}"
    )

    _age: Variable[int] = new(0)
    _age_error: QLabel = new(
        "Must be positive",
        visible="{_age <= 0}"
    )
```

## Property Bindings vs Content Bindings

| Feature | Property Binding | Content Binding |
|---------|-----------------|-----------------|
| Purpose | Control widget state | Control widget content |
| Parameters | `visible=`, `enabled=` | `bind=` |
| Result type | Boolean | String/value |
| Example | `visible="_show"` | `bind="Hello {_name}"` |

```python
@widget
class Comparison(Widget):
    _name: Variable[str] = new("")
    _show_greeting: Variable[bool] = new(True)

    # Content binding - what to display
    _greeting: QLabel = new(bind="Hello, {_name}!")

    # Property binding - whether to show it
    _panel: QWidget = new(visible="_show_greeting")
```

## Reactivity

Property bindings automatically re-evaluate when any referenced Variable changes:

```python
@widget
class ReactiveExample(Widget):
    _a: Variable[bool] = new(True)
    _b: Variable[bool] = new(True)

    # Re-evaluates when either _a or _b changes
    _widget: QLabel = new(visible="{_a and _b}")

    def toggle_a(self) -> None:
        self._a = not self._a.value  # Widget visibility updates
```

## See Also

- [Variables](variables.md) - Reactive state management
- [Bindings](bindings.md) - Content bindings with `bind=`
- [Format Expressions](format-expressions.md) - Expression syntax
