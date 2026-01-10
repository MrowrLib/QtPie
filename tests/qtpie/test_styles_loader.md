# Stylesheet Loader Tests

## Loading from Local QSS Files

Loads Qt stylesheets from filesystem paths. Returns empty string if file doesn't exist.

```python
qss_file = tmp_path / "styles.qss"
qss_file.write_text("QPushButton { color: red; }")

result = load_stylesheet(qss_path=str(qss_file))

assert_that(result).contains("QPushButton")
assert_that(result).contains("color: red")
```

## Loading from QRC Resources

Loads Qt stylesheets from Qt resource files (`:` prefix paths). Returns empty string if resource doesn't exist.

```python
with (
    patch("qtpie.styles.loader.QFile", return_value=mock_file),
    patch("qtpie.styles.loader.QTextStream", return_value=mock_stream),
):
    result = load_stylesheet(qrc_path=":/styles/test_styles.qss")

assert_that(result).contains("QPushButton")
assert_that(result).contains("background-color: red")
```

## Fallback Behavior

Local file takes precedence when both paths provided. Falls back to QRC if local file doesn't exist.

```python
# Local exists - uses local, ignores QRC
result = load_stylesheet(
    qss_path=str(local_qss),
    qrc_path=":/styles/test_styles.qss",
)

# Local missing - falls back to QRC
result = load_stylesheet(
    qss_path="/nonexistent/styles.qss",
    qrc_path=":/styles/test_styles.qss",
)
```
