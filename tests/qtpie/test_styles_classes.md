# QtPie CSS Class Helpers

This documents the CSS class manipulation utilities in `qtpie.styles`.

## Overview

QtPie provides a set of helper functions for managing CSS classes on Qt widgets, enabling dynamic styling similar to web frameworks. All functions work with any `QWidget`.

## Imports

```python
from qtpie.styles import (
    add_class,
    add_classes,
    get_classes,
    has_any_class,
    has_class,
    remove_class,
    replace_class,
    set_classes,
    toggle_class,
)
```

## get_classes / set_classes

Get or set the full list of CSS classes on a widget.

```python
set_classes(widget, ["foo", "bar"])
classes = get_classes(widget)  # ["foo", "bar"]
```

Optional `refresh=False` parameter skips style refresh (for batch operations).

## add_class / add_classes

Add one or more CSS classes. Duplicates are automatically prevented.

```python
add_class(widget, "highlight")
add_classes(widget, ["active", "visible"])
```

## has_class / has_any_class

Check if a widget has specific CSS classes.

```python
if has_class(widget, "active"):
    ...

if has_any_class(widget, ["error", "warning"]):
    ...
```

## remove_class

Remove a CSS class from a widget. No-op if class not present.

```python
remove_class(widget, "highlight")
```

## replace_class

Swap one class for another, preserving position in the class list.

```python
replace_class(widget, "old-class", "new-class")
```

## toggle_class

Add class if absent, remove if present.

```python
toggle_class(widget, "expanded")  # Adds "expanded"
toggle_class(widget, "expanded")  # Removes "expanded"
```

## Typical Usage Pattern

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click", classes=["primary"])

    def on_click(self):
        toggle_class(self._button, "active")
```
