# Menu Separators in QtPie

Menu separators are visual dividers between groups of menu actions. QtPie provides a declarative syntax using bare type annotations.

## Basic Separator Syntax

Separators are declared as bare type annotations (no `= new()` needed). The field name typically uses underscores.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator
    exit_action: QAction = new("E&xit")
```

## Separator Naming Conventions

Field names for separators can use any underscore pattern. Common conventions:

```python
_: Separator      # Single underscore
__: Separator     # Double underscore
___: Separator    # Triple underscore
____: Separator   # Four underscores (most common)
_1: Separator     # Numbered for multiple separators
_2: Separator
```

## Multiple Separators

Multiple separators can be added to create visual groupings. Each needs a unique field name.

```python
@menu(text="&Edit")
class EditMenu(Menu):
    cut: QAction = new("Cut")
    copy: QAction = new("Copy")
    paste: QAction = new("Paste")
    _1: Separator
    _2: Separator  # Multiple separators allowed
    select_all: QAction = new("Select All")
```

## Declaration Order

Separators appear in the order they are declared, interleaved with actions.

```python
@menu(text="&File")
class FileMenu(Menu):
    action1: QAction = new("One")
    _1: Separator
    action2: QAction = new("Two")
    _2: Separator
    action3: QAction = new("Three")
# Results in: One, [separator], Two, [separator], Three
```

## Grouping Actions

The primary use case is grouping related menu actions together.

```python
@menu(text="&Edit")
class EditMenu(Menu):
    cut: QAction = new("Cut")
    copy: QAction = new("Copy")
    ____: Separator
    paste: QAction = new("Paste")
    delete: QAction = new("Delete")
```

## Required Import

```python
from qtpie.menu import Separator
```
