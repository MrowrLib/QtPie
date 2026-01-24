# Auto-New Feature

The auto-new feature allows bare type annotations to automatically instantiate widgets, reducing boilerplate for simple widget declarations.

## Basic Auto-New (Bare Type Annotations)

Bare type annotations automatically create widget instances without needing `new()`.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    label: QLabel       # Auto-instantiates QLabel()
    button: QPushButton # Auto-instantiates QPushButton()
    input: QLineEdit    # Auto-instantiates QLineEdit()
```

## Explicit new() with Arguments

Use explicit `new()` when you need to pass constructor arguments or configure the widget.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    label: QLabel = new("Hello World")  # Passes text to QLabel constructor
```

## Opt-Out with none()

Use `none()` to explicitly prevent auto-instantiation when you want a placeholder or will assign later.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    placeholder: QLabel = none()  # No instance created, attribute won't exist
```

## Variables Are Unaffected

`Variable[T]` types follow their own rules - they require explicit `new()` with a default value.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    count: Variable[int] = new(42)  # Explicit Variable with default
    required: Variable[int]         # Bare Variable = required binding (not auto-newed)
```

## Mixed Patterns

All patterns work together in the same class.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    bare_label: QLabel                  # Auto-new
    explicit_label: QLabel = new("Hi")  # Explicit with args
    skipped: QLabel = none()            # Opt-out
    count: Variable[int] = new(100)     # Variable with default
```
