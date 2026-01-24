# Menu Sections in QtPie

Menu sections provide labeled groupings within menus, creating visual headers that organize related actions.

## Basic Section Declaration

Sections are declared as class attributes with the `Section` type annotation. The field name uses triple underscores as delimiters.

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent___: Section
    file1: QAction = new("file1.txt")
```

The section text is derived from the field name by stripping underscores and converting to title case.

## Snake Case to Title Case Conversion

Field names using snake_case are automatically converted to Title Case for display.

```python
___recent_files___: Section  # Displays as "Recent Files"
```

## Explicit Section Text

Override the auto-derived text using `new()` with a positional argument or `text=` keyword.

```python
# Positional argument
___recent___: Section = new("Recently Opened Files")

# Keyword argument
___recent___: Section = new(text="Recent Items")
```

## Multiple Sections

Sections group subsequent actions until the next section. Declaration order is preserved.

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent___: Section
    file1: QAction = new("file1.txt")
    file2: QAction = new("file2.txt")
    ___favorites___: Section
    fav1: QAction = new("favorite.txt")
```

This creates two groups: "Recent" containing file1 and file2, followed by "Favorites" containing fav1.

## Key Imports

```python
from qtpie import Menu, menu, new
from qtpie.menu import Section
```

## Notes

- Sections are implemented as disabled `QAction` items via Qt's `addSection()` method
- The triple underscore convention (`___name___`) distinguishes sections from regular fields
- Reactive `bind=` for dynamic section titles is documented but not yet implemented
