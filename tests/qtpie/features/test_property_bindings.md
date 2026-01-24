# Property Bindings Feature Documentation

This document describes the `visible=` and `enabled=` property binding patterns in QtPie.

## Overview

Property bindings allow reactive control of widget visibility and enabled state. Both `visible=` and `enabled=` accept either:
- A Variable name (string) for simple boolean binding
- An expression string in `{...}` format for computed bindings

---

## visible= Binding with Variable

Bind widget visibility directly to a `Variable[bool]`.

```python
_show: Variable[bool] = new(True)
label: QLabel = new("Hello", visible="_show")
```

Visibility updates automatically when the Variable changes:

```python
instance._show.value = False  # label becomes hidden
instance._show.value = True   # label becomes visible
```

---

## enabled= Binding with Variable

Bind widget enabled state directly to a `Variable[bool]`.

```python
_can_click: Variable[bool] = new(True)
button: QPushButton = new("Click", enabled="_can_click")
```

---

## Expression Bindings

Use `{...}` syntax for computed visibility/enabled based on expressions.

### Comparison Expressions

```python
_count: Variable[int] = new(0)
label: QLabel = new("Has items", visible="{_count > 0}")
```

### Length/Function Expressions

```python
_name: Variable[str] = new("")
submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")
```

### Boolean Logic (and/or/not)

```python
_logged_in: Variable[bool] = new(False)
_is_admin: Variable[bool] = new(False)
admin_panel: QLabel = new("Admin", visible="{_logged_in and _is_admin}")
```

```python
_has_warning: Variable[bool] = new(False)
_has_error: Variable[bool] = new(False)
alert: QLabel = new("Alert", visible="{_has_warning or _has_error}")
```

```python
_loading: Variable[bool] = new(True)
content: QLabel = new("Content", visible="{not _loading}")
```

### Equality Expressions

```python
_status: Variable[str] = new("pending")
confirm: QPushButton = new("Confirm", enabled="{_status == 'ready'}")
```

### Multi-Variable Expressions

Expressions can reference multiple Variables; updates when any changes:

```python
_a: Variable[int] = new(0)
_b: Variable[int] = new(0)
label: QLabel = new("Sum", visible="{_a + _b > 5}")
```

---

## Multiple Property Bindings

A widget can have both `visible=` and `enabled=` bindings:

```python
_show: Variable[bool] = new(True)
_allow: Variable[bool] = new(True)
button: QPushButton = new("Action", visible="_show", enabled="_allow")
```

With expressions:

```python
_count: Variable[int] = new(0)
_name: Variable[str] = new("")
button: QPushButton = new(
    "Submit",
    visible="{_count > 0}",
    enabled="{len(_name) > 0}",
)
```

---

## Enum Expressions in Widget[T] Records

Visibility expressions can reference enum fields from a record type.

### Enum `in` List Expression

```python
class BodyType(Enum):
    NONE = "none"
    TEXT = "text"
    JSON = "json"

@widget(record=RequestRecord(body_type=BodyType.JSON))
class TestWidget(Widget[RequestRecord]):
    label: QLabel = new(
        "Text Editor",
        visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
    )
```

### Reactive Updates on Record Field Change

```python
instance.record.body_type = BodyType.FORM_DATA  # visibility updates automatically
```

---

## Widget Field Shadowing Record Field

When a widget field has the same name as a record field, expressions reference the **record field value**, not the widget:

```python
@widget(record=RequestRecord(body_type=BodyType.JSON))
class TestWidget(Widget[RequestRecord]):
    # QComboBox named same as record field
    body_type: QComboBox = new(bind=BodyType, selectedItem="body_type")

    # Expression uses record.body_type, not the QComboBox
    text_editor: QLabel = new(
        "Editor",
        visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
    )
```

---

## Deferred Record Binding with Child Widgets

Child widgets with `bind="record"` receive the parent's record. Visibility expressions re-evaluate after binding completes:

```python
@widget
class ChildWidget(Widget[RequestRecord]):
    editor: QLabel = new(
        "Editor",
        visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
    )

@widget(record=RequestRecord(body_type=BodyType.JSON))
class ParentWidget(Widget[RequestRecord]):
    child: ChildWidget = new(bind="record")
```

---

## Optional Chaining in Expressions

Use `?.` for safe navigation through optional nested paths:

```python
@widget(record=RequestWithAuth(auth=AuthSettings(type=AuthType.BASIC)))
class TestWidget(Widget[RequestWithAuth]):
    basic_label: QLabel = new("Basic", visible="{auth?.type == AuthType.BASIC}")
```

When the intermediate value is `None`, the expression evaluates safely:

```python
@widget(record=RequestWithAuth(auth=None))
class TestWidget(Widget[RequestWithAuth]):
    # auth is None, so auth?.type is None, expression evaluates to False
    basic_label: QLabel = new("Basic", visible="{auth?.type == AuthType.BASIC}")
```

---

## Variable Name Conventions

- Variables can use underscore prefix (`_show`) or not (`show_it`)
- Binding without underscore falls back to `_name` lookup:

```python
_enabled_flag: Variable[bool] = new(True)
button: QPushButton = new("Test", enabled="enabled_flag")  # looks up _enabled_flag
```

---

## Multiple Widgets Same Variable

Multiple widgets can bind to the same Variable:

```python
_show: Variable[bool] = new(True)
label1: QLabel = new("One", visible="_show")
label2: QLabel = new("Two", visible="_show")
```
