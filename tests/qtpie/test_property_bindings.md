# Property Bindings

## Simple Variable Binding

Bind widget properties (`visible=`, `enabled=`) to Variable fields using field name strings.

```python
@widget
class TestWidget(Widget):
    _is_visible: Variable[bool] = new(True)
    _label: QLabel = new("Hello", visible="_is_visible")

w = TestWidget()
w._is_visible.value = False  # Label hides automatically
```

```python
@widget
class TestWidget(Widget):
    _can_click: Variable[bool] = new(True)
    _button: QPushButton = new("Click me", enabled="_can_click")

w = TestWidget()
w._can_click.value = False  # Button disables automatically
```

## Expression Bindings

Bind properties to Python expressions using `{...}` syntax. Supports comparisons, boolean logic, function calls.

```python
@widget
class TestWidget(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new("Has items", visible="{_count > 0}")

w = TestWidget()
w._count.value = 1  # Label becomes visible
```

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")
```

```python
@widget
class TestWidget(Widget):
    _logged_in: Variable[bool] = new(False)
    _is_admin: Variable[bool] = new(False)
    _admin_panel: QLabel = new("Admin Panel", visible="{_logged_in and _is_admin}")
```

## Multiple Property Bindings

Apply multiple property bindings to the same widget.

```python
@widget
class TestWidget(Widget):
    _show: Variable[bool] = new(True)
    _allow: Variable[bool] = new(True)
    _button: QPushButton = new("Action", visible="_show", enabled="_allow")
```

## Reactive Decorator Properties

Make `@widget` decorator properties reactive using expression syntax.

```python
@widget(windowTitle="{_title}")
class TestWidget(Widget):
    _title: Variable[str] = new("Initial Title")

w = TestWidget()
w._title.value = "Updated Title"  # Window title updates automatically
```

```python
@widget(windowTitle="{_app_name} - {_filename}")
class TestWidget(Widget):
    _app_name: Variable[str] = new("Editor")
    _filename: Variable[str] = new("untitled.txt")
```

## Raw Reactive Types

Bind to raw `Observable`, `ObservableList`, `ObservableDict`, and `ObservableProxy` class attributes without wrapping in `Variable`.

```python
@widget
class TestWidget(Widget):
    can_submit: Observable[bool] = Observable(False)
    _button: QPushButton = new("Submit", enabled="{can_submit.get()}")

w = TestWidget()
w.can_submit.set(True)  # Button enables
```

```python
@widget
class TestWidget(Widget):
    items: ObservableList[str] = ObservableList()
    _label: QLabel = new("Has items", visible="{len(items) > 0}")

w = TestWidget()
w.items.append("item1")  # Label becomes visible
```

```python
@widget
class TestWidget(Widget):
    settings: ObservableProxy[_TestSettings] = ObservableProxy(_TestSettings())
    _button: QPushButton = new("Action", enabled="{settings.enabled}")

w = TestWidget()
w.settings.enabled = True  # Button enables
```

```python
@widget
class TestWidget(Widget):
    is_ready: Observable[bool] = Observable(False)
    items: ObservableList[str] = ObservableList()
    _button: QPushButton = new(
        "Submit",
        enabled="{is_ready.get() and len(items) > 0}",
    )
```
