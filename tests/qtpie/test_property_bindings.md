# Property Bindings Test Summary

## `visible=` with Simple Variable

Bind widget visibility to a `Variable[bool]`. When the variable changes, the widget automatically shows/hides.

```python
@widget
class TestWidget(Widget):
    _is_visible: Variable[bool] = new(True)
    _label: QLabel = new("Hello", visible="_is_visible")

w = TestWidget()
w._is_visible.value = False  # Label hides automatically
```

## `enabled=` with Simple Variable

Bind widget enabled state to a `Variable[bool]`. When the variable changes, the widget automatically enables/disables.

```python
@widget
class TestWidget(Widget):
    _can_click: Variable[bool] = new(True)
    _button: QPushButton = new("Click me", enabled="_can_click")

w = TestWidget()
w._can_click.value = False  # Button disables automatically
```

## Expression Bindings

Use `{...}` expressions for computed visibility/enabled state based on variable values.

```python
@widget
class TestWidget(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new("Has items", visible="{_count > 0}")

    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")

    _logged_in: Variable[bool] = new(False)
    _is_admin: Variable[bool] = new(False)
    _admin_panel: QLabel = new("Admin Panel", visible="{_logged_in and _is_admin}")
```

## Multiple Property Bindings

Apply both `visible=` and `enabled=` to the same widget. Each binding updates independently.

```python
@widget
class TestWidget(Widget):
    _show: Variable[bool] = new(True)
    _allow: Variable[bool] = new(True)
    _button: QPushButton = new("Action", visible="_show", enabled="_allow")
```

## Reactive Decorator Properties

Decorator kwargs can reference variables to create reactive properties like `windowTitle`.

```python
@widget(windowTitle="{_title}")
class TestWidget(Widget):
    _title: Variable[str] = new("Initial Title")

w = TestWidget()
w._title.value = "Updated Title"  # Window title updates automatically

@widget(windowTitle="{_app_name} - {_filename}")
class TestWidget(Widget):
    _app_name: Variable[str] = new("Editor")
    _filename: Variable[str] = new("untitled.txt")
```

## Raw Observable Types

Property bindings work with raw `Observable`, `ObservableList`, `ObservableDict`, and `ObservableProxy` types, not just `Variable`.

```python
@widget
class TestWidget(Widget):
    # Raw Observable
    can_submit: Observable[bool] = Observable(False)
    _button: QPushButton = new("Submit", enabled="{can_submit.get()}")

    # Raw ObservableList
    items: ObservableList[str] = ObservableList()
    _label: QLabel = new("Has items", visible="{len(items) > 0}")

    # Raw ObservableProxy
    settings: ObservableProxy[_TestSettings] = ObservableProxy(_TestSettings())
    _button: QPushButton = new("Action", enabled="{settings.enabled}")

    # Combined expression
    is_ready: Observable[bool] = Observable(False)
    items: ObservableList[str] = ObservableList()
    _submit: QPushButton = new("Submit", enabled="{is_ready.get() and len(items) > 0}")
```
