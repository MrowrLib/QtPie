# Property Bindings

Property bindings control widget properties reactively using `visible=` and `enabled=` parameters. These bindings automatically update the widget when the bound variable changes, enabling declarative control over UI behavior.

## Basic visible= Binding

The `visible=` parameter controls whether a widget is shown or hidden:

```python
@widget
class BasicVisibility(Widget):
    _show_panel: Variable[bool] = new(True)
    _panel: QLabel = new("Panel content", visible="_show_panel")

    def toggle_panel(self):
        self._show_panel.value = not self._show_panel.value
        # Panel automatically shows/hides
```

### Starting Hidden

Widgets can start hidden and be shown later:

```python
@widget
class StartHidden(Widget):
    _show_advanced: Variable[bool] = new(False)
    _advanced_panel: QLabel = new("Advanced options", visible="_show_advanced")

    def show_advanced(self):
        self._show_advanced.value = True  # Panel appears
```

## Basic enabled= Binding

The `enabled=` parameter controls whether a widget accepts user interaction:

```python
@widget
class BasicEnabled(Widget):
    _can_submit: Variable[bool] = new(True)
    _submit_btn: QPushButton = new("Submit", enabled="_can_submit")

    def disable_button(self):
        self._can_submit.value = False
        # Button becomes grayed out and non-clickable
```

### Starting Disabled

Widgets can start disabled:

```python
@widget
class StartDisabled(Widget):
    _is_ready: Variable[bool] = new(False)
    _start_btn: QPushButton = new("Start", enabled="_is_ready")

    def on_ready(self):
        self._is_ready.value = True  # Button becomes clickable
```

## Expression Bindings

Use `{expression}` syntax for conditional property bindings:

### Comparison Expressions

```python
@widget
class Comparisons(Widget):
    _count: Variable[int] = new(0)

    # Show only when count > 0
    _items_label: QLabel = new("Items available", visible="{_count > 0}")

    # Enable only when count < 10
    _add_btn: QPushButton = new("Add", enabled="{_count < 10}")

    def add_item(self):
        self._count.value += 1
        # _items_label appears when count becomes 1
        # _add_btn disables when count reaches 10
```

### Length Checks

```python
@widget
class LengthChecks(Widget):
    _name: Variable[str] = new("")

    # Enable submit only when name is not empty
    _submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")

    # Show error when name is empty
    _error: QLabel = new("Name required!", visible="{len(_name) == 0}")
```

### Boolean Logic

Use `and`, `or`, and `not` operators:

```python
@widget
class BooleanLogic(Widget):
    _logged_in: Variable[bool] = new(False)
    _is_admin: Variable[bool] = new(False)

    # Visible only when BOTH conditions are true
    _admin_panel: QLabel = new(
        "Admin Panel",
        visible="{_logged_in and _is_admin}"
    )

    # Loading state management
    _loading: Variable[bool] = new(True)
    _content: QLabel = new("Content", visible="{not _loading}")
    _spinner: QLabel = new("Loading...", visible="_loading")
```

### OR Logic

```python
@widget
class OrLogic(Widget):
    _has_permission: Variable[bool] = new(False)
    _is_owner: Variable[bool] = new(False)

    # Enable if user has permission OR is the owner
    _edit_btn: QPushButton = new(
        "Edit",
        enabled="{_has_permission or _is_owner}"
    )
```

### String Comparisons

```python
@widget
class StringComparisons(Widget):
    _status: Variable[str] = new("active")

    # Show badge only when status is "active"
    _active_badge: QLabel = new("Active", visible="{_status == 'active'}")

    # Show warning when status is "error"
    _error_badge: QLabel = new("Error", visible="{_status == 'error'}")
```

## Multiple Property Bindings

A single widget can have multiple property bindings:

```python
@widget
class MultipleBindings(Widget):
    _show: Variable[bool] = new(True)
    _allow: Variable[bool] = new(True)

    # Control both visibility AND enabled state
    _action_btn: QPushButton = new(
        "Action",
        visible="_show",
        enabled="_allow"
    )

# Examples:
w = MultipleBindings()

# Button is visible and enabled
w._show.value = False  # Button hidden (but still enabled)
w._show.value = True   # Button visible again
w._allow.value = False # Button visible but disabled
```

## Variable Name Patterns

QtPie looks up variables with or without underscore prefix:

```python
@widget
class VariableNames(Widget):
    # With underscore (conventional)
    _is_visible: Variable[bool] = new(True)
    _label1: QLabel = new("Test", visible="_is_visible")

    # Without underscore (also works)
    show_it: Variable[bool] = new(True)
    _label2: QLabel = new("Test", visible="show_it")

    # The binding will find _show_it if show_it is not found
    _enabled_flag: Variable[bool] = new(True)
    _button: QPushButton = new("Test", enabled="enabled_flag")
```

## Reactive Decorator Properties

Widget decorator parameters can be reactive too:

```python
@widget(windowTitle="{_title}")
class DynamicTitle(Widget):
    _title: Variable[str] = new("Initial Title")

    def update_title(self):
        self._title.value = "New Title"
        # Window title updates automatically
```

### Format Strings in Decorator

```python
@widget(windowTitle="Count: {_count}")
class CounterWindow(Widget):
    _count: Variable[int] = new(0)

    def increment(self):
        self._count.value += 1
        # Window title updates to "Count: 1", "Count: 2", etc.
```

### Multiple Variables in Decorator

```python
@widget(windowTitle="{_app_name} - {_filename}")
class EditorWindow(Widget):
    _app_name: Variable[str] = new("Editor")
    _filename: Variable[str] = new("untitled.txt")

# Window title is "Editor - untitled.txt"
w = EditorWindow()
w._filename.value = "document.md"
# Window title updates to "Editor - document.md"
```

### Static Properties Still Work

Non-reactive properties work as before:

```python
@widget(windowTitle="My App")
class StaticTitle(Widget):
    pass

# Window title is always "My App"
```

## Common Patterns

### Form Validation

```python
@widget
class FormValidation(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    # Show errors when fields are empty
    _username_error: QLabel = new(
        "Username required",
        visible="{len(_username) == 0}"
    )
    _password_error: QLabel = new(
        "Password required",
        visible="{len(_password) == 0}"
    )

    # Enable submit only when both fields are filled
    _submit: QPushButton = new(
        "Submit",
        enabled="{len(_username) > 0 and len(_password) > 0}"
    )
```

### Loading States

```python
@widget
class LoadingStates(Widget):
    _is_loading: Variable[bool] = new(False)

    # Show spinner while loading
    _spinner: QLabel = new("Loading...", visible="_is_loading")

    # Hide content while loading
    _content: QLabel = new("Data", visible="{not _is_loading}")

    # Disable actions while loading
    _refresh: QPushButton = new("Refresh", enabled="{not _is_loading}")
```

### Conditional UI Elements

```python
@widget
class ConditionalUI(Widget):
    _user_type: Variable[str] = new("guest")

    # Show different content based on user type
    _guest_welcome: QLabel = new(
        "Welcome, guest!",
        visible="{_user_type == 'guest'}"
    )
    _admin_panel: QLabel = new(
        "Admin Panel",
        visible="{_user_type == 'admin'}"
    )
```

### Progressive Disclosure

```python
@widget
class ProgressiveDisclosure(Widget):
    _show_advanced: Variable[bool] = new(False)

    # Toggle button
    _toggle: QPushButton = new("Show Advanced", clicked="toggle_advanced")

    # Advanced panel
    _advanced: QWidget = new(visible="_show_advanced")

    def toggle_advanced(self):
        self._show_advanced.value = not self._show_advanced.value
        self._toggle.setText(
            "Hide Advanced" if self._show_advanced.value else "Show Advanced"
        )
```

### Permission-Based UI

```python
@widget
class PermissionBased(Widget):
    _can_edit: Variable[bool] = new(False)
    _can_delete: Variable[bool] = new(False)

    _edit_btn: QPushButton = new("Edit", enabled="_can_edit")
    _delete_btn: QPushButton = new("Delete", enabled="_can_delete")

    # Only admins see the admin section
    _can_admin: Variable[bool] = new(False)
    _admin_section: QWidget = new(visible="_can_admin")
```

## Edge Cases and Gotchas

### isVisible() vs isHidden()

Qt's `isVisible()` returns `False` if ANY parent is hidden, even if the widget itself has `setVisible(True)`. Use this carefully when checking widget state in tests. The binding sets the widget's own visibility correctly.

### NOT Operator

The `not` operator works in expressions:

```python
@widget
class NotOperator(Widget):
    _loading: Variable[bool] = new(True)

    # Content visible when NOT loading
    _content: QLabel = new("Content", visible="{not _loading}")
```

### Complex Expressions

Keep expressions readable. If they get too complex, use a method:

```python
@widget
class ComplexLogic(Widget):
    _status: Variable[str] = new("pending")
    _has_permission: Variable[bool] = new(False)
    _is_owner: Variable[bool] = new(False)

    # BAD - hard to read
    _btn: QPushButton = new(
        "Action",
        enabled="{(_status == 'ready' or _status == 'waiting') and (_has_permission or _is_owner)}"
    )

    # GOOD - use a method
    _btn2: QPushButton = new("Action", enabled="{can_perform_action()}")

    def can_perform_action(self) -> bool:
        status_ok = self._status.value in ("ready", "waiting")
        authorized = self._has_permission.value or self._is_owner.value
        return status_ok and authorized
```

## Best Practices

1. **Use descriptive variable names** - `_show_advanced` is clearer than `_visible`
2. **Keep expressions simple** - Complex logic belongs in methods
3. **Use boolean variables for toggles** - More readable than string comparisons
4. **Combine with format bindings** - Use both property and text bindings together
5. **Test edge cases** - Ensure expressions handle empty strings, zero values, etc.
6. **Leverage NOT operator** - Use `{not _loading}` instead of tracking opposite states

## Comparison with Manual Updates

### Without Property Bindings

```python
@widget
class Manual(Widget):
    _count: Variable[int] = new(0)
    _submit: QPushButton = new("Submit")

    def __init__(self):
        super().__init__()
        self._count.observe(self._update_button)
        self._update_button(self._count.value)

    def _update_button(self, count: int) -> None:
        self._submit.setEnabled(count > 0)
```

### With Property Bindings

```python
@widget
class Declarative(Widget):
    _count: Variable[int] = new(0)
    _submit: QPushButton = new("Submit", enabled="{_count > 0}")

# Much cleaner and declarative!
```
