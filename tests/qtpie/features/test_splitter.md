# QSplitter Support in QtPie

QtPie provides declarative support for `QSplitter` widgets using the `splitter=` parameter in `new()`.

## Declaring a Splitter

Create a `QSplitter` field with orientation:

```python
_splitter: QSplitter = new(Qt.Orientation.Horizontal)
```

## Adding Widgets to a Splitter

Use `splitter=` parameter referencing the splitter field name:

```python
_splitter: QSplitter = new(Qt.Orientation.Horizontal)
left: QLabel = new("Left", splitter="_splitter")
right: QLabel = new("Right", splitter="_splitter")
```

Widgets are added in declaration order.

## Vertical Splitter

```python
_splitter: QSplitter = new(Qt.Orientation.Vertical)
top: QLabel = new("Top", splitter="_splitter")
bottom: QLabel = new("Bottom", splitter="_splitter")
```

## Layout Behavior

Splitters integrate with the parent layout. Widgets assigned to a splitter are excluded from the default layout:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    header: QLabel = new("Header")           # Added to vertical layout
    _splitter: QSplitter = new(Qt.Orientation.Horizontal)  # Added to vertical layout
    left: QLabel = new("Left", splitter="_splitter")       # NOT in vertical layout
    right: QLabel = new("Right", splitter="_splitter")     # NOT in vertical layout
    footer: QLabel = new("Footer")           # Added to vertical layout
```

Result: Layout contains `[header, _splitter, footer]`. Splitter contains `[left, right]`.

## Multiple Splitters

Multiple independent splitters are supported:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    _top_splitter: QSplitter = new(Qt.Orientation.Horizontal)
    top_left: QLabel = new("Top Left", splitter="_top_splitter")
    top_right: QLabel = new("Top Right", splitter="_top_splitter")

    _bottom_splitter: QSplitter = new(Qt.Orientation.Horizontal)
    bottom_left: QLabel = new("Bottom Left", splitter="_bottom_splitter")
    bottom_right: QLabel = new("Bottom Right", splitter="_bottom_splitter")
```

## Key Points

- `splitter=` takes a string referencing the splitter field name (e.g., `"_splitter"`)
- Widgets are added to the splitter in field declaration order
- Splitter-assigned widgets are automatically excluded from the parent layout
- The splitter itself is added to the parent layout in its declaration position
