# QtPie Styles Loader - Usage Patterns

This documents the stylesheet loading feature in QtPie, based on test analysis.

## Core Function: `load_stylesheet`

Import from `qtpie.styles`:

```python
from qtpie.styles import load_stylesheet
```

## Loading from Local QSS Files

Load stylesheets from filesystem paths using `qss_path`:

```python
result = load_stylesheet(qss_path="/path/to/styles.qss")
```

Returns the file content as a string, or empty string if file doesn't exist.

## Loading from QRC Resources

Load stylesheets from Qt Resource Collection (QRC) using `qrc_path`:

```python
result = load_stylesheet(qrc_path=":/styles/app.qss")
```

QRC paths use the `:/` prefix convention. Returns empty string if resource doesn't exist.

## Fallback Behavior (Local to QRC)

Provide both paths for automatic fallback - local file takes precedence:

```python
result = load_stylesheet(
    qss_path="/path/to/styles.qss",    # Tried first
    qrc_path=":/styles/fallback.qss",  # Used if local missing
)
```

This pattern enables development-mode file editing with production QRC fallback.

## Empty/Missing Handling

All missing paths return empty string (no exceptions):

```python
result = load_stylesheet()  # Returns ""
result = load_stylesheet(qss_path="/nonexistent.qss")  # Returns ""
```
