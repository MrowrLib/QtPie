# Checkable Menu Actions

This document describes how to create toggleable menu actions that can be bound to reactive Variables for two-way state synchronization.

## Basic Checkable Action

Use `checkable=True` to create a toggleable menu action.

```python
@menu(text="&View")
class ViewMenu(Menu):
    word_wrap: QAction = new("Word Wrap", checkable=True)
```

## Initially Checked State

Use `checked=True` to start the action in checked state.

```python
word_wrap: QAction = new("Word Wrap", checkable=True, checked=True)
```

## Two-Way Variable Binding

Bind a checkable action to a `Variable[bool]` for reactive two-way synchronization. Changes to either the Variable or the action update the other.

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)
    word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")
```

The action's initial state is set from the Variable's value. Toggling the action updates the Variable, and changing the Variable updates the action.

## Toggle Callback

Use `toggled=` to connect a method that receives the checked state when the action is toggled.

```python
@menu(text="&View")
class ViewMenu(Menu):
    word_wrap: QAction = new("Word Wrap", checkable=True, toggled="on_toggled")

    def on_toggled(self, checked: bool) -> None:
        print(f"Word wrap is now: {checked}")
```

## Combined Binding and Callback

`checked=` (Variable binding) and `toggled=` (callback) can be used together.

```python
@menu(text="&View")
class ViewMenu(Menu):
    _enabled: Variable[bool] = new(False)
    feature: QAction = new(
        "Feature",
        checkable=True,
        checked="_enabled",
        toggled="on_toggled",
    )

    def on_toggled(self, checked: bool) -> None:
        self.callback_count += 1
```

## Multiple Independent Checkable Actions

Each checkable action can have its own independent Variable binding.

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)
    _line_numbers: Variable[bool] = new(True)
    _minimap: Variable[bool] = new(False)

    word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")
    line_numbers: QAction = new("Line Numbers", checkable=True, checked="_line_numbers")
    minimap: QAction = new("Minimap", checkable=True, checked="_minimap")
```

## Summary of Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `checkable=True` | bool | Makes the action toggleable |
| `checked=True` | bool | Initial checked state (static) |
| `checked="_var"` | str | Two-way bind to a `Variable[bool]` |
| `toggled="method"` | str | Callback method receiving `checked: bool` |
