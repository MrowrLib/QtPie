# Size Parameter Feature

The `size=` parameter allows setting initial widget dimensions declaratively on `@widget`, `@window`, and `@app` decorators.

## Basic Usage - Widget/Window Size

Set initial dimensions using a `(width, height)` tuple:

```python
@widget(size=(800, 600))
class MyWidget(Widget):
    pass
```

```python
@window(size=(1920, 1080))
class MainWindow(Window):
    pass
```

## App Window Size

For `@app` decorated classes, `size=` sets the dimensions of the auto-created window:

```python
@app(size=(1024, 768))
class TestApp(AppBase):
    _label: QLabel = new("Hello")
```

The size is applied to `instance.window`.

## Key Points

- Accepts a tuple: `size=(width, height)`
- Uses Qt's `resize()` under the hood
- Optional parameter - without it, Qt's default sizing applies
- Works with any dimension values (small or large)
