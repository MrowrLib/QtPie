# Color Scheme Feature Documentation

This document describes the color scheme functionality in QtPie for controlling dark/light mode appearance.

## Imports

All color scheme functionality is imported from `qtpie.styles`:

```python
from qtpie.styles import (
    ColorScheme,
    enable_dark_mode,
    enable_light_mode,
    set_color_scheme,
)
```

## ColorScheme Enum

The `ColorScheme` enum provides type-safe color scheme values:

```python
ColorScheme.Dark
ColorScheme.Light
```

## Setting Color Scheme with `set_color_scheme()`

The primary API for setting color schemes. Works with or without an existing QApplication.

### Basic Usage

```python
set_color_scheme(ColorScheme.Dark)
set_color_scheme(ColorScheme.Light)
```

### With Explicit App Reference

```python
set_color_scheme(ColorScheme.Dark, qapp)
```

## Convenience Helpers

Simple one-liner functions for common cases:

### Enable Dark Mode

```python
enable_dark_mode()
```

### Enable Light Mode

```python
enable_light_mode()
```

## Pending Color Scheme

When called before a QApplication exists, the color scheme is stored as "pending" and applied when the app is created. This allows setting the color scheme early in application initialization.

```python
# Before QApplication exists
set_color_scheme(ColorScheme.Dark)  # Stores pending

# Later, when app is created, dark mode is automatically applied
```

## Getting Configured Scheme

To query the currently configured (possibly pending) color scheme:

```python
from qtpie.styles.color_scheme import get_configured_color_scheme

scheme = get_configured_color_scheme()  # Returns ColorScheme enum
```

## Display Requirements

Some color scheme operations require a real display (not offscreen). The offscreen platform returns `ColorScheme.Unknown` when querying. For testing with display-dependent features:

```bash
uv run pytest tests/qtpie/test_color_scheme.py -v --onscreen
```
