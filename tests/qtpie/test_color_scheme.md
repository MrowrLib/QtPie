# Color Scheme Tests

## Setting Color Schemes

Set dark or light mode on Qt applications. When an app exists, applies immediately via Qt API. When no app exists yet, stores the scheme for later application and sets platform-specific environment variables.

```python
# With existing app
set_color_scheme(ColorScheme.Dark)
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)

set_color_scheme(ColorScheme.Light)
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Light)
```

```python
# Without app - stores pending and sets env vars on Windows
with patch.object(QApplication, "instance", return_value=None):
    set_color_scheme(ColorScheme.Dark)
    assert_that(get_configured_color_scheme()).is_equal_to(ColorScheme.Dark)
    assert_that(os.environ.get("QT_QPA_PLATFORM")).is_equal_to("windows:darkmode=2")
```

## Convenience Helpers

Shorthand functions for enabling dark or light mode without specifying the enum.

```python
enable_dark_mode()
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Dark)

enable_light_mode()
assert_that(qapp.styleHints().colorScheme()).is_equal_to(Qt.ColorScheme.Light)
```
