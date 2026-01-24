# QtPie Theme System Usage Patterns

This document describes the theme discovery and management system in QtPie, extracted from `test_themes.py`.

## Core Types

The theme system uses these main types from `qtpie.styles.themes`:

- `Theme` - Represents a single theme (QSS file or SCSS folder)
- `ThemeMode` - Enum with `Dark` and `Light` variants
- `ThemeSet` - Collection of themes discovered from a directory

```python
from qtpie.styles.themes import Theme, ThemeMode, ThemeSet, detect_mode
```

## Theme Mode Detection

The `detect_mode()` function infers whether a theme is dark or light based on naming conventions.

### Exact match (case-insensitive)
```python
detect_mode("dark")   # ThemeMode.Dark
detect_mode("Light")  # ThemeMode.Light
```

### Suffix pattern: `*-dark` or `*-light`
```python
detect_mode("solarized-dark")   # ThemeMode.Dark
detect_mode("catppuccin-light") # ThemeMode.Light
```

### Prefix pattern: `dark-*` or `light-*`
```python
detect_mode("dark-contrast")    # ThemeMode.Dark
detect_mode("light-high-contrast") # ThemeMode.Light
```

### Default behavior
Unknown theme names default to Dark mode:
```python
detect_mode("monokai")  # ThemeMode.Dark
detect_mode("dracula")  # ThemeMode.Dark
```

## SCSS Entry Point Detection

The `find_scss_entry_point()` function finds the main SCSS file in a theme folder.

### Priority: `main.scss` or `theme.scss`
```python
entry = find_scss_entry_point(Path("themes/monokai"))
# Returns path to main.scss or theme.scss
```

### Partials are ignored
Files prefixed with `_` (like `_colors.scss`) are SCSS partials and are not considered entry points.

## ThemeSet - Theme Discovery

`ThemeSet` automatically discovers themes from a directory. It finds:
- `.qss` files (Qt Style Sheets)
- Folders containing SCSS entry points

```python
theme_set = ThemeSet(Path("./themes"))
```

### Accessing discovered themes
```python
theme_set.theme_names   # Sorted list of theme names
theme_set.themes        # Dict[str, Theme]
```

### Getting a specific theme
```python
theme = theme_set.get_theme("dark")
theme.name      # "dark"
theme.mode      # ThemeMode.Dark
theme.is_scss   # False for .qss files, True for SCSS folders
```

## Setting the Active Theme

```python
theme_set = ThemeSet(Path("./themes"))

# Initially no theme is active
theme_set.current_theme      # None
theme_set.current_theme_name # None

# Set theme by name
theme_set.set_theme("dark")  # Returns True on success
theme_set.current_theme_name # "dark"

# Returns False for unknown themes
theme_set.set_theme("nonexistent")  # False
```

## Dynamic Theme Refresh

Call `refresh()` to re-scan the themes directory for changes:

```python
theme_set = ThemeSet(themes_dir)
# ... files added/removed ...
theme_set.refresh()  # Re-discovers themes
```

If the current theme is removed, `current_theme` becomes `None` after refresh.

## QRC Resource Support

ThemeSet supports Qt Resource System (QRC) paths:

```python
theme_set = ThemeSet(":/themes")
theme_set.is_qrc  # True

theme_set = ThemeSet(Path("./themes"))
theme_set.is_qrc  # False
```

## Theme Properties

A `Theme` object exposes:

| Property | Description |
|----------|-------------|
| `name` | Theme identifier (filename without extension or folder name) |
| `mode` | `ThemeMode.Dark` or `ThemeMode.Light` |
| `is_scss` | `True` for SCSS folders, `False` for QSS files |
| `entry_point` | Path to SCSS entry file (only for SCSS themes) |

## File System Conventions

### QSS Themes
Place `.qss` files directly in the themes directory:
```
themes/
  dark.qss
  light.qss
```

### SCSS Themes
Create folders with a `main.scss` or `theme.scss` entry point:
```
themes/
  monokai/
    main.scss
    _colors.scss
  nord-light/
    theme.scss
    _variables.scss
```
