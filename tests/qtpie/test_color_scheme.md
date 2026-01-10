# Color Scheme Tests

## Color Scheme Setting

Set dark or light color scheme via `set_color_scheme()`. When a QApplication exists, it applies immediately via Qt API. When no app exists, it stores the scheme for later application and sets Windows environment variables.

```python
set_color_scheme(ColorScheme.Dark)
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)
```

```python
# With explicit app parameter
set_color_scheme(ColorScheme.Dark, qapp)
```

```python
# Without app - stores pending and sets env var on Windows
with patch.object(QApplication, "instance", return_value=None):
    set_color_scheme(ColorScheme.Dark)
    assert_that(get_configured_color_scheme()).is_equal_to(ColorScheme.Dark)
    assert_that(os.environ.get("QT_QPA_PLATFORM")).is_equal_to("windows:darkmode=2")
```

## Convenience Helpers

`enable_dark_mode()` and `enable_light_mode()` are shortcuts for `set_color_scheme()`.

```python
enable_dark_mode()
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)
```

```python
enable_light_mode()
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Light)
```
