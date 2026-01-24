# Stylesheets Feature Documentation

QtPie provides CSS-like styling capabilities for Qt widgets through stylesheets, CSS classes, and object names.

## App Stylesheet

Apply global stylesheets to an app using the `stylesheet=` parameter on `@app`.

```python
@app(stylesheet="QLabel { color: red; }")
class MyApp(AppBase):
    label: QLabel = new("Hello")
```

The stylesheet uses Qt's CSS-like syntax and is stored in the app config's `widget_props`.

## CSS Classes

### On App/Window

Set CSS classes on the window using `classes=` on `@app`.

```python
@app(classes=["dark-theme", "compact"])
class MyApp(AppBase):
    label: QLabel = new("Hello")
```

### On Widgets

Set CSS classes on individual widgets using `classes=` on `new()`.

```python
primary: QLabel = new("Primary", classes=["btn", "btn-primary"])
```

Classes can be retrieved using `get_classes()` from `qtpie.styles`.

## Object Names

Object names enable CSS selectors like `#my-widget { ... }`.

### On App/Window

Set window objectName using `name=` on `@app`. Defaults to class name if not specified.

```python
@app(name="main-app")
class MyApp(AppBase):
    label: QLabel = new("Hello")
# a.window.objectName() == "main-app"
```

### On Widgets

Set widget objectName using `name=` on `new()`. Defaults to field name if not specified.

```python
title: QLabel = new("Title", name="page-title")
# a.title.objectName() == "page-title"
```

## Combined Styling

All styling parameters can be combined for full control.

```python
@app(
    name="styled-app",
    classes=["theme-dark"],
    stylesheet="QLabel { padding: 10px; }",
)
class MyApp(AppBase):
    header: QLabel = new("Header", name="main-header", classes=["large"])
    content: QLabel = new("Content", classes=["body-text"])
```

## Key Conventions

- `stylesheet=` on `@app` applies globally to all widgets
- `classes=` sets CSS class list (array of strings)
- `name=` sets Qt objectName for CSS `#id` selectors
- Default objectName: class name for app/window, field name for widgets
- Use `qtpie.styles.get_classes()` to retrieve classes from a widget
