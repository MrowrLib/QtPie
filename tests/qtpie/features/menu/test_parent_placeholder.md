# Parent Placeholder in Menu Expressions

The `#parent` placeholder allows menus to reference variables from their parent Window. This enables reactive bindings between menu actions and window-level state.

## Basic `#parent` Usage

Menus can bind `enabled=` or `visible=` to parent window Variables using `{#parent._variable}` syntax.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("Save", enabled="{#parent._is_dirty}")

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new()
```

When `app._is_dirty.value = True`, the Save action becomes enabled automatically.

## Visible Binding with `#parent`

Same pattern works for `visible=` to show/hide menu actions based on parent state.

```python
@menu(text="&Advanced")
class AdvancedMenu(Menu):
    debug: QAction = new("Debug", visible="{#parent._show_debug}")
```

## Complex Expressions

Multiple parent variables can be combined in a single expression using boolean operators.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("Save", enabled="{#parent._is_dirty and #parent._can_save}")
```

The action is only enabled when both conditions are true.

## Variable Naming Conventions

Both underscore-prefixed and non-prefixed variable names work with `#parent`.

```python
# With underscore (private convention)
enabled="{#parent._enabled}"

# Without underscore (public convention)
enabled="{#parent.is_ready}"
```

## Multiple Menus Sharing Parent State

Multiple menus can bind to the same parent Variable - all update when it changes.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("Save", enabled="{#parent._is_dirty}")

@menu(text="&Edit")
class EditMenu(Menu):
    undo: QAction = new("Undo", enabled="{#parent._is_dirty}")

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()
```

When `_is_dirty` changes, both Save and Undo actions update simultaneously.

## Key Points

- `#parent` always refers to the Window containing the Menu
- Bindings are reactive - actions update automatically when parent Variables change
- Works with both `enabled=` and `visible=` bindings
- Supports complex boolean expressions with multiple parent variables
- Mixed `#parent` and local menu variables in the same expression is not yet supported
