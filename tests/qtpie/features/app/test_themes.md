# Theme System Usage Patterns

The QtPie theme system provides runtime theming with support for QSS and SCSS stylesheets.

## Theme Runtime API

The primary interface consists of global functions for theme management.

### Initializing Themes

```python
from qtpie.styles.theme_runtime import init_themes

init_themes(themes_directory, qapp, initial_theme="dark")
```

### Getting Available Themes

```python
from qtpie.styles import get_themes

themes = get_themes()  # Returns list like ["dark", "light", "monokai"]
```

### Getting Current Theme

```python
from qtpie.styles import get_theme

current = get_theme()  # Returns theme name like "dark", or None
```

### Switching Themes

```python
from qtpie.styles import set_theme

success = set_theme("light")  # Returns True on success, False if theme unknown
```

### Detecting Dark Mode

```python
from qtpie.styles import is_dark_theme

if is_dark_theme():
    # Theme is dark variant
```

Dark mode detection is based on theme naming conventions - themes named "dark" or ending in "-dark" are dark, themes named "light" or ending in "-light" are light.

## ThemeSet Class

Direct theme set manipulation for advanced use cases.

```python
from qtpie.styles.themes import ThemeSet, ThemeMode

theme_set = ThemeSet(themes_directory)
theme_set.set_theme("dark")

# Access current theme properties
name = theme_set.current_theme_name  # "dark"
mode = theme_set.current_theme.mode  # ThemeMode.Dark

# Lookup theme by name
theme = theme_set.get_theme("dark")
```

## Theme Directory Structure

Themes are discovered from a directory containing theme folders:

```
themes/
  dark/           # QSS theme - contains dark.qss
  light/          # QSS theme - contains light.qss
  monokai/        # SCSS theme - contains main.scss
  _shared/        # Shared SCSS partials (underscore prefix = not a theme)
```

## SCSS Support

SCSS themes are automatically compiled. Themes can import from shared directories.

```scss
// monokai/main.scss
@import "../_shared/shared";
@import "colors";

* {
    background-color: $bg;
    border-color: $shared-color;
}
```

## Cleanup (Testing)

For test isolation, cleanup global theme state between tests.

```python
from qtpie.styles.theme_runtime import cleanup_themes

cleanup_themes()  # Clears all global theme state
```
