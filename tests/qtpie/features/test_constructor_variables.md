# Constructor Variables

This document describes how to pass initial values to `Variable[T]` fields through widget/dialog constructors.

## Static Value Assignment

Pass static values (int, str, bool) to Variables via constructor kwargs.

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)

instance = Counter(_count=42)  # Sets _count to 42
```

Constructor values override the default from `new()`:

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(100)  # Default 100

instance = Example(_count=42)  # Overridden to 42
```

Pass multiple variables at once:

```python
instance = MyWidget(_count=42, _name="test", _enabled=True)
```

Partial override - only override some variables while keeping others at default:

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(10)
    _name: Variable[str] = new("default")

instance = Example(_count=99)  # _count=99, _name="default"
```

## Bare Variables (Required Fields)

Declare a Variable without `= new()` to create a required field that must be provided via constructor.

```python
@widget
class Item(Widget):
    kind: Variable[str]  # Bare - required at construction

instance = Item(kind="Collection")  # Must provide kind
```

Mix bare (required) and defaulted variables:

```python
@widget
class Item(Widget):
    kind: Variable[str]              # Required
    count: Variable[int] = new(0)    # Optional with default

instance = Item(kind="Request")  # kind required, count defaults to 0
```

## Observable Binding

Pass an `Observable` to share state between the widget and external code.

```python
external: Observable[int] = Observable(42)
instance = Counter(_count=external)

# Bidirectional sync
external.set(100)                # instance._count.value is now 100
instance._count.value = 200      # external.get() is now 200
```

## Variable Binding

Pass a `Variable` from one widget to another to share the same underlying Observable.

```python
instance1 = Counter()
instance1._count.value = 42

instance2 = Counter(_count=instance1._count)  # Shares the Observable

# Bidirectional sync
instance1._count.value = 100  # instance2._count.value is also 100
instance2._count.value = 200  # instance1._count.value is also 200
```

This also works with bare variables:

```python
@widget
class Item(Widget):
    kind: Variable[str]  # Bare

instance1 = Item(kind="First")
instance2 = Item(kind=instance1.kind)  # Shares Observable

instance1.kind.value = "Changed"  # Both instances see "Changed"
```

## Format Binding Resolution

Constructor-provided values resolve in format bindings immediately.

### In `bind=` kwargs

```python
@widget
class Editor(Widget):
    kind: Variable[str] = new("")
    label: QLabel = new(bind="New {kind}")

instance = Editor(kind="Collection")
# label shows "New Collection"
```

### In decorator kwargs

```python
@widget(windowTitle="Edit {kind}")
class Editor(Widget):
    kind: Variable[str] = new("")

instance = Editor(kind="Request")
# Window title is "Edit Request"
```

### With bare variables

```python
@dialog(title="New {kind}")
class NewDialog(Dialog):
    kind: Variable[str]  # Bare - required

instance = NewDialog(kind="Collection")
# Dialog title is "New Collection"
```

### Reactive updates after construction

Bindings continue to update reactively after initial construction:

```python
instance = Editor(kind="A")         # label shows "Type: A"
instance.kind.value = "B"           # label updates to "Type: B"
```

### In Variable[T, W] widget kwargs

Format bindings work in widget kwargs like `placeholderText=` and `label=`:

```python
@widget
class Form(Widget):
    kind: Variable[str] = new("")
    name: Variable[str, QLineEdit] = new("")(placeholderText="Enter {kind} name...")

instance = Form(kind="Request")
# Placeholder shows "Enter Request name..."

instance.kind.value = "Collection"
# Placeholder updates to "Enter Collection name..."
```

## Dialog show_dialog() Forwarding

`show_dialog()` class method forwards kwargs to the dialog constructor.

```python
@dialog
class NewItemDialog(Dialog):
    kind: Variable[str] = new("")
    _ok: DialogButton

# Equivalent to NewItemDialog(kind="Collection").exec()
result = NewItemDialog.show_dialog(kind="Collection")
```

Works with record types too:

```python
@dialog
class EditDialog(Dialog[Person]):
    kind: Variable[str] = new("")
    name: QLineEdit = new()
    _ok: DialogButton

result = EditDialog.show_dialog(Person("Alice", 30), kind="User")
# Dialog has record=Person("Alice", 30) and kind="User"
```
