# Window Central Widget Feature

This document describes how QtPie's `Window` class handles central widget setup, layouts, and configuration.

## Overview

`Window` wraps `QMainWindow` and automatically creates a central widget to hold declared fields. All QWidget fields are placed into this central widget's layout.

## Basic Window Declaration

Use the `@window` decorator to create a window with the `title=` parameter.

```python
@window(title="My Application")
class MainWindow(Window):
    label: QLabel = new("Hello")
```

Fields become accessible as instance attributes, and a central widget is auto-created.

## Layout Types

Windows support the same layout options as widgets via the `layout=` parameter.

### Vertical Layout (Default)

```python
@window(title="Test")
class TestWindow(Window):
    label1: QLabel = new("First")
    label2: QLabel = new("Second")
```

### Horizontal Layout

```python
@window(title="Test", layout="horizontal")
class TestWindow(Window):
    btn1: QPushButton = new("A")
    btn2: QPushButton = new("B")
```

### Form Layout

Use `layout="form"` with `label=` on fields to create form rows.

```python
@window(title="Test", layout="form")
class TestWindow(Window):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")
```

### Grid Layout

Use `layout="grid"` with `grid=(row, col)` or `grid=(row, col, rowspan, colspan)`.

```python
@window(title="Test", layout="grid")
class TestWindow(Window):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
    c: QLabel = new("C", grid=(1, 0, 1, 2))  # Span 2 columns
```

## Variable[T, W] in Windows

Windows support `Variable[T, W]` fields which create both reactive state and a widget.

```python
@window(title="Test")
class TestWindow(Window):
    _name: Variable[str, QLineEdit] = new("")
```

Access the value via `._name.value` and the widget via `._name.widget`.

### Variable with Form Label

```python
@window(title="Test", layout="form")
class TestWindow(Window):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")
```

## Window Properties

### Title

```python
@window(title="My Application")
class TestWindow(Window): ...
```

### Object Name

Use `name=` to set a custom objectName, otherwise it defaults to the class name.

```python
@window(title="Test", name="main-window")
class TestWindow(Window): ...
```

### CSS Classes

```python
@window(title="Test", classes=["dark-theme", "compact"])
class TestWindow(Window): ...
```

## Layout Margins

Control central widget layout margins with the `margins=` parameter.

### Uniform Margins

```python
@window(title="Test", margins=20)
class TestWindow(Window): ...
```

### Individual Margins

Pass a tuple of `(left, top, right, bottom)`.

```python
@window(title="Test", margins=(5, 10, 15, 20))
class TestWindow(Window): ...
```
