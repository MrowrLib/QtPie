# Property Bindings in QtPie

This document describes the `visible=` and `enabled=` property binding features in QtPie, extracted from test patterns.

## Simple Variable Binding

Bind widget properties directly to a `Variable[bool]` by name.

```python
@widget
class TestWidget(Widget):
    _is_visible: Variable[bool] = new(True)
    _label: QLabel = new("Hello", visible="_is_visible")
```

The binding is reactive - when `_is_visible.value` changes, the widget visibility updates automatically.

## Enabled Binding

Same pattern works for `enabled=` property on interactive widgets.

```python
@widget
class TestWidget(Widget):
    _can_click: Variable[bool] = new(True)
    _button: QPushButton = new("Click me", enabled="_can_click")
```

## Expression Bindings

Wrap Python expressions in `{}` for computed boolean values.

### Comparison Expressions

```python
_count: Variable[int] = new(0)
_label: QLabel = new("Has items", visible="{_count > 0}")
```

### Function Calls (len, etc.)

```python
_name: Variable[str] = new("")
_submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")
```

### Boolean Operators (and, or, not)

```python
_logged_in: Variable[bool] = new(False)
_is_admin: Variable[bool] = new(False)
_admin_panel: QLabel = new("Admin Panel", visible="{_logged_in and _is_admin}")
```

```python
_loading: Variable[bool] = new(True)
_content: QLabel = new("Content", visible="{not _loading}")
```

### String Comparison

```python
_status: Variable[str] = new("active")
_badge: QLabel = new("Active", visible="{_status == 'active'}")
```

## Multiple Property Bindings

A single widget can have both `visible=` and `enabled=` bindings.

```python
@widget
class TestWidget(Widget):
    _show: Variable[bool] = new(True)
    _allow: Variable[bool] = new(True)
    _button: QPushButton = new("Action", visible="_show", enabled="_allow")
```

## Underscore Prefix Flexibility

Variable names with or without underscore prefix work - QtPie handles the lookup.

```python
# Both work:
show_it: Variable[bool] = new(True)
_label: QLabel = new("Test", visible="show_it")

# OR reference without underscore:
_enabled_flag: Variable[bool] = new(True)
_button: QPushButton = new("Test", enabled="enabled_flag")
```

## Reactive Decorator Properties

The `@widget` decorator itself can have reactive properties using format strings.

### Reactive Window Title

```python
@widget(windowTitle="{_title}")
class TestWidget(Widget):
    _title: Variable[str] = new("Initial Title")
```

### Multiple Variables in Decorator

```python
@widget(windowTitle="{_app_name} - {_filename}")
class TestWidget(Widget):
    _app_name: Variable[str] = new("Editor")
    _filename: Variable[str] = new("untitled.txt")
```

## Raw Reactive Type Bindings

Besides `Variable`, you can bind to raw observant types: `Observable`, `ObservableList`, `ObservableDict`, `ObservableProxy`.

### Observable

```python
can_submit: Observable[bool] = Observable(False)
_button: QPushButton = new("Submit", enabled="{can_submit.get()}")
```

### ObservableList

```python
items: ObservableList[str] = ObservableList()
_label: QLabel = new("Has items", visible="{len(items) > 0}")
```

### ObservableDict

```python
config: ObservableDict[str, int] = ObservableDict()
_button: QPushButton = new("Has Config", enabled="{len(config) > 0}")
```

### ObservableProxy

```python
@dataclass
class Settings:
    enabled: bool = False

settings: ObservableProxy[Settings] = ObservableProxy(Settings())
_button: QPushButton = new("Action", enabled="{settings.enabled}")
```

## Combining Reactive Types

Expressions can mix different reactive types together.

```python
_name: Variable[str] = new("")
feature_enabled: Observable[bool] = Observable(True)
_button: QPushButton = new(
    "Submit",
    enabled="{len(_name) > 0 and feature_enabled.get()}",
)
```

## Key Conventions

1. **Simple binding**: Use variable name as string (`visible="_flag"`)
2. **Expression binding**: Wrap in braces (`visible="{len(_name) > 0}"`)
3. **Boolean result**: Expressions must evaluate to `bool`
4. **Reactive**: All bindings auto-update when referenced variables change
5. **Multiple bindings**: Combine `visible=` and `enabled=` on same widget
6. **Decorator props**: Use `{_var}` syntax in `@widget(windowTitle="{_title}")`
