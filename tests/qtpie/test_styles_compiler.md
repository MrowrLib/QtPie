# SCSS to QSS Compiler - Usage Patterns

The `compile_scss` function from `qtpie.styles` compiles SCSS stylesheets to Qt-compatible QSS format.

## Basic Compilation

Compile a single SCSS file to QSS output:

```python
from qtpie.styles import compile_scss

compile_scss(
    scss_path="path/to/styles.scss",
    qss_path="path/to/output.qss",
)
```

## SCSS Syntax for Qt Widgets

Use Qt widget class names as selectors with standard SCSS properties:

```scss
QPushButton {
    background-color: blue;
    padding: 8px 16px;
}

QLabel {
    color: white;
}
```

## SCSS Variables

Define reusable variables using standard SCSS `$variable` syntax:

```scss
$primary: #007bff;
$padding: 8px;

QPushButton {
    background-color: $primary;
    padding: $padding;
}
```

## Import Partials with Search Paths

Use `@import` to include partials and specify search directories:

```python
compile_scss(
    scss_path="main.scss",
    qss_path="output.qss",
    search_paths=["path/to/partials"],
)
```

In `main.scss`:
```scss
@import "variables";  // Resolves from search_paths
@import "buttons";
```

Partials use underscore prefix convention (e.g., `_variables.scss`).

## Multiple Search Paths

Provide multiple search directories for modular organization:

```python
compile_scss(
    scss_path="main.scss",
    qss_path="output.qss",
    search_paths=[
        "path/to/core",
        "path/to/themes",
    ],
)
```

Variables defined in earlier search paths are available to later imports:

```scss
// core/_variables.scss
$base-size: 16px;
$accent-color: #ff6600;

// themes/_theme.scss (uses variables from core)
QWidget {
    font-size: $base-size;
}

QPushButton {
    background-color: $accent-color;
}
```

## Directory Auto-Creation

Output directories are created automatically if they do not exist:

```python
compile_scss(
    scss_path="styles.scss",
    qss_path="nested/deep/output.qss",  # Directories created
)
```

## Recommended File Organization

```
resources/
  themes/
    _shared/
      _variables.scss
      _buttons.scss
    dark.scss     # @import "variables"; @import "buttons";
    light.scss
```
