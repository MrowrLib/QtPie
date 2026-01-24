# Menu Bar Integration in QtPie Windows

This document describes how to use menu bars with QtPie's `Window` class.

## Overview

Windows automatically integrate `Menu` fields into the window's menu bar. Menus are defined as separate classes using the `@menu` decorator and added to windows as fields.

## Defining a Menu

Use the `@menu` decorator to create a menu class. The `text=` parameter sets the menu title (use `&` for keyboard accelerators).

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    exit_action: QAction = new("E&xit")
```

## Adding Menus to a Window

Declare menu fields in your `Window` class. They are automatically added to the menu bar.

```python
@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()
    content: QLabel = new("Content")
```

## Multiple Menus

Multiple menus appear in the menu bar in field declaration order.

```python
@window(title="Test App")
class TestWindow(Window):
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()
    help_menu: HelpMenu = new()
```

## Accessing Menu Actions

Access actions via nested attribute access on the window instance.

```python
w = TestWindow()
w.file_menu.new_action.trigger()
w.file_menu.save_action.text()
```

## Menu Field Position

Menu fields can be declared before or after widget fields - they always go to the menu bar, while widgets go to the central layout.

```python
@window(title="Test")
class TestWindow(Window):
    label: QLabel = new("Label")      # Goes to central widget
    file_menu: FileMenu = new()       # Goes to menu bar
```

## Connecting Action Signals

Use `triggered=` to connect menu actions to handler methods within the Menu class.

```python
@menu(text="&File")
class FileMenu(Menu):
    action: QAction = new("Action", triggered="on_action")

    def on_action(self) -> None:
        print("Action triggered!")
```

## Accessing Parent Window from Menu

Menus can access their parent window via the `_parent_window` attribute.

```python
@menu(text="&File")
class FileMenu(Menu):
    action: QAction = new("Action", triggered="toggle_flag")

    def toggle_flag(self) -> None:
        parent = getattr(self, "_parent_window", None)
        if parent is not None:
            parent.flag = True
```

## Reactive Menu Visibility

Bind menu visibility to Variables using `visible=`. This controls `menuAction().isVisible()`.

```python
@window(title="Test")
class TestWindow(Window):
    _show_file_menu: Variable[bool] = new(True)
    file_menu: FileMenu = new(visible="_show_file_menu")
```

## Expression Binding for Visibility

Use format string expressions for complex visibility conditions.

```python
@window(title="Test")
class TestWindow(Window):
    _data_loaded: Variable[bool] = new(False)
    edit_menu: EditMenu = new(visible="{_data_loaded}")
```

## Initially Hidden Menus

Menus can start hidden and become visible later via reactive bindings.

```python
@window(title="Test")
class TestWindow(Window):
    _show_view: Variable[bool] = new(False)
    view_menu: ViewMenu = new(visible="_show_view")
```

## Windows Without Menus

Windows without any Menu fields simply have an empty menu bar.

```python
@window(title="Simple Window")
class TestWindow(Window):
    label: QLabel = new("Just a label")
```
