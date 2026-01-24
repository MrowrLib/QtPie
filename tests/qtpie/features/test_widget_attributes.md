# Widget Attributes Feature

This document covers the `attributes=` and `styledBackground=` parameters available on `@widget`, `@window`, and `@dialog` decorators for setting Qt widget attributes declaratively.

## styledBackground= Shorthand

A convenience parameter for the common `WA_StyledBackground` attribute, which enables custom background painting via stylesheets.

```python
@widget(styledBackground=True)
class StyledWidget(Widget):
    pass
```

By default, `styledBackground` is `False`. This shorthand avoids the verbose `attributes={Qt.WidgetAttribute.WA_StyledBackground: True}`.

## attributes= Dict

Set multiple widget attributes with explicit `True`/`False` values using a dictionary.

```python
@widget(attributes={
    Qt.WidgetAttribute.WA_StyledBackground: True,
    Qt.WidgetAttribute.WA_TranslucentBackground: True,
})
class TranslucentWidget(Widget):
    pass
```

Mixed values are supported - set some attributes to `True` and others to `False`:

```python
@widget(attributes={
    Qt.WidgetAttribute.WA_StyledBackground: True,
    Qt.WidgetAttribute.WA_NoSystemBackground: False,
})
class MixedWidget(Widget):
    pass
```

## attributes= Tuple

For enabling multiple attributes (all set to `True`), use a tuple shorthand:

```python
@widget(attributes=(
    Qt.WidgetAttribute.WA_StyledBackground,
    Qt.WidgetAttribute.WA_TranslucentBackground,
))
class MultiAttributeWidget(Widget):
    pass
```

## Combining styledBackground= with attributes=

Both parameters can be used together. The `styledBackground=` parameter is applied after `attributes=`, so it takes precedence for `WA_StyledBackground`:

```python
@widget(
    styledBackground=True,
    attributes={Qt.WidgetAttribute.WA_TranslucentBackground: True},
)
class CombinedWidget(Widget):
    pass
```

## Applies To

These parameters work consistently across:
- `@widget` decorator
- `@window` decorator
- `@dialog` decorator
