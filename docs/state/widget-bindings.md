# Widget Bindings

Widget bindings pass reactive state from parent widgets to child widgets. This enables composable, reusable components - like React props for Qt.

## Basic Example

```python
from qtpie import Widget, Variable, new, widget

@widget
class CounterDisplay(Widget):
    count: Variable[int]  # Required from parent
    _label: QLabel = new(bind="Count: {count}")

@widget
class App(Widget):
    _my_count: Variable[int] = new(0)
    display: CounterDisplay = new(count="_my_count")
    _button: QPushButton = new("+1", clicked="increment")

    def increment(self) -> None:
        self._my_count += 1  # Display updates automatically!
```

## Required vs Optional Bindings

### Required Bindings

Variables declared without `= new()` are **required** - the parent must provide them:

```python
@widget
class ChildWidget(Widget):
    theme: Variable[str]  # Required!
    count: Variable[int]  # Required!
```

Missing required bindings raise an error at instantiation:

```python
@widget
class Parent(Widget):
    child: ChildWidget = new()  # ERROR: Missing 'theme' and 'count'
```

### Optional Bindings

Variables with `= new(default)` are **optional** - they use the default if not provided:

```python
@widget
class ChildWidget(Widget):
    theme: Variable[str] = new("dark")  # Optional, defaults to "dark"
    count: Variable[int]  # Still required
```

## Two-Way Bindings

Widget bindings are **two-way** by default. Changes in either direction propagate:

```python
@widget
class Child(Widget):
    count: Variable[int]

@widget
class Parent(Widget):
    _count: Variable[int] = new(0)
    child: Child = new(count="_count")

parent = Parent()

# Parent → Child
parent._count = 42
assert parent.child.count.value == 42

# Child → Parent
parent.child.count = 100
assert parent._count.value == 100
```

## Expression Bindings (One-Way)

Use `{expression}` for computed, one-way bindings:

```python
@widget
class SubmitButton(Widget):
    enabled: Variable[bool]
    _btn: QPushButton = new("Submit", enabled="enabled")

@widget
class Form(Widget):
    _name: Variable[str] = new("")

    # One-way computed binding
    submit: SubmitButton = new(enabled="{len(_name) > 0}")
```

The `enabled` Variable updates when `_name` changes, but changes to `enabled` don't affect `_name`.

## Literal Values

Strings that don't start with `_` or contain `{}` are literal values:

```python
@widget
class Themed(Widget):
    theme: Variable[str]

@widget
class App(Widget):
    _dynamic: Variable[str] = new("dark")

    # Reactive binding
    widget1: Themed = new(theme="_dynamic")

    # Static literal value
    widget2: Themed = new(theme="light")
```

## Nested Hierarchies

Bindings pass through any number of widget levels:

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class Child(Widget):
    theme: Variable[str]  # Receive from parent
    grandchild: GrandChild = new(theme="theme")  # Pass to child

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

parent = Parent()
parent._theme = "light"
# GrandChild label now shows "Theme: light"
```

## Sibling Widgets

Multiple children can share the same binding:

```python
@widget
class Display(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class Dashboard(Widget):
    _shared: Variable[str] = new("Hello")

    # All three share the same state
    display1: Display = new(value="_shared")
    display2: Display = new(value="_shared")
    display3: Display = new(value="_shared")

dashboard = Dashboard()
dashboard._shared = "Updated"
# All three displays now show "Updated"
```

## Multiple Bindings

Pass multiple Variables to a child:

```python
@widget
class StatusWidget(Widget):
    name: Variable[str]
    count: Variable[int]
    enabled: Variable[bool]

    _label: QLabel = new(
        bind="{name}: {count} ({'on' if enabled else 'off'})"
    )

@widget
class App(Widget):
    _name: Variable[str] = new("Status")
    _count: Variable[int] = new(0)
    _enabled: Variable[bool] = new(True)

    status: StatusWidget = new(
        name="_name",
        count="_count",
        enabled="_enabled"
    )
```

## Diamond Pattern

Multiple branches can share a common root:

```python
@widget
class Leaf(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class BranchA(Widget):
    value: Variable[str]
    leaf: Leaf = new(value="value")

@widget
class BranchB(Widget):
    value: Variable[str]
    leaf: Leaf = new(value="value")

@widget
class Root(Widget):
    _shared: Variable[str] = new("data")
    branch_a: BranchA = new(value="_shared")
    branch_b: BranchB = new(value="_shared")

# Both branches stay synchronized
root = Root()
root._shared = "new"
# Both branch_a.leaf and branch_b.leaf show "new"
```

## Widget Bindings vs Content Bindings

| Feature | Widget Bindings | Content Bindings |
|---------|-----------------|------------------|
| Purpose | Pass state to children | Display Variable in widget |
| Syntax | `child: Child = new(var="_var")` | `_label: QLabel = new(bind="_var")` |
| Direction | Two-way (or one-way with expressions) | Variable → Widget |
| Use case | Component composition | Displaying values |

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(0)

    # Content binding - display the value
    _label: QLabel = new(bind="Count: {_count}")

    # Widget binding - pass to child
    counter: CounterWidget = new(count="_count")
```

## Naming Convention

Common pattern: parent uses `_underscore`, child uses `no_underscore`:

```python
@widget
class Child(Widget):
    theme: Variable[str]  # No underscore - "public" binding point

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")  # Underscore - "private" state
    child: Child = new(theme="_theme")
```

This makes the binding relationship clear in code.

## Nested Record Editors

For complex objects, use `Variable[T, Widget[T]]` to create a child widget that edits the record:

```python
from dataclasses import dataclass

@dataclass
class Address:
    street: str = ""
    city: str = ""

@widget(layout="form")
class AddressEditor(Widget[Address]):
    street: QLineEdit = new(label="Street")
    city: QLineEdit = new(label="City")

@widget
class PersonForm(Widget):
    _name: Variable[str, QLineEdit] = new("")
    _address: Variable[Address, AddressEditor] = new(default=Address())
```

The child widget's `record` and the parent's Variable share the same state - changes in either direction propagate automatically.

### Accessing the Widget

```python
def focus_address(self) -> None:
    self._address.widget.street.setFocus()
```

### List of Editors

Create multiple editor widgets for a list:

```python
@dataclass
class Contact:
    name: str = ""
    email: str = ""

@widget(layout="form")
class ContactEditor(Widget[Contact]):
    name: QLineEdit = new()
    email: QLineEdit = new()

@widget
class ContactList(Widget):
    _contacts: Variable[list[Contact], ContactEditor] = new([
        Contact("Alice", "alice@example.com"),
        Contact("Bob", "bob@example.com")
    ])
```

This creates one `ContactEditor` per contact. Adding/removing contacts adds/removes editors.

## See Also

- [Variables](variables.md) - Reactive state basics
- [Bindings](bindings.md) - Content bindings with `bind=`
- [Format Expressions](format-expressions.md) - Expression syntax
- [Records](../data/records.md) - Widget[T] record types
