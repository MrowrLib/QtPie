# @entrypoint Decorator Tests Summary

## Config Storage

The `@entrypoint` decorator stores configuration on the decorated function or class as an `EntryConfig` instance.

```python
@entrypoint(dark_mode=True, title="Test App")
def my_main() -> QLabel:
    return QLabel("Hi")

assert_that(hasattr(my_main, ENTRY_CONFIG_ATTR)).is_true()
config = getattr(my_main, ENTRY_CONFIG_ATTR)
assert_that(config.dark_mode).is_true()
assert_that(config.title).is_equal_to("Test App")
```

```python
@entrypoint(dark_mode=True, size=(1024, 768))
@widget
class TestWidget(Widget):
    label: QLabel = new("Test")

config = getattr(TestWidget, ENTRY_CONFIG_ATTR)
assert_that(config.dark_mode).is_true()
assert_that(config.size).is_equal_to((1024, 768))
```

## Stylesheet Loading

Loads and applies QSS or SCSS stylesheets to the application.

```python
qss_file = tmp_path / "styles.qss"
qss_file.write_text("QWidget { background-color: green; }")

config = EntryConfig(stylesheet=str(qss_file))
_apply_stylesheet(qapp, config)

assert_that(qapp.styleSheet()).contains("background-color: green")
```

```python
scss_file = tmp_path / "styles.scss"
scss_file.write_text("$color: purple; QWidget { color: $color; }")

config = EntryConfig(stylesheet=str(scss_file))
_apply_stylesheet(qapp, config)

assert_that(qapp.styleSheet()).contains("purple")
```

## QRC Stylesheet Support

Loads stylesheets from Qt Resource files (QRC paths starting with `:/`).

```python
mock_file = MagicMock()
mock_file.open.return_value = True

mock_stream = MagicMock()
mock_stream.readAll.return_value = "QPushButton { color: red; }"

with (
    patch("qtpie.entrypoint.QFile", return_value=mock_file),
    patch("qtpie.entrypoint.QTextStream", return_value=mock_stream),
):
    result = _load_qrc_stylesheet(":/styles/test.qss")

assert_that(result).contains("QPushButton")
assert_that(result).contains("color: red")
```

## Stylesheet Watching

Returns a watcher that monitors stylesheet files for changes and auto-reloads them.

```python
qss_file = tmp_path / "styles.qss"
qss_file.write_text("QWidget { color: red; }")

config = EntryConfig(stylesheet=str(qss_file), watch_stylesheet=True)
watcher = _apply_stylesheet(qapp, config)

assert_that(watcher).is_not_none()
assert_that(type(watcher).__name__).is_equal_to("QssWatcher")
```

```python
scss_file = tmp_path / "styles.scss"
scss_file.write_text("QWidget { color: red; }")

config = EntryConfig(stylesheet=str(scss_file), watch_stylesheet=True)
watcher = _apply_stylesheet(qapp, config)

assert_that(watcher).is_not_none()
assert_that(type(watcher).__name__).is_equal_to("ScssWatcher")
```

## Auto-Run Detection

The decorator checks if it should automatically run the app (only if module is `__main__` and no QApplication exists).

```python
def dummy() -> None:
    pass

dummy.__module__ = "__main__"
assert_that(_is_main_module(dummy)).is_true()

dummy.__module__ = "myapp.main"
assert_that(_is_main_module(dummy)).is_false()
```

```python
# Even with __main__ module, should return False because app exists
def dummy() -> None:
    pass

dummy.__module__ = "__main__"
assert_that(_should_auto_run(dummy)).is_false()  # QApplication exists
```

## Function/Class Preservation

The decorator preserves the original function or class, keeping them callable and usable.

```python
@entrypoint
def my_main() -> str:
    return "hello"

assert_that(callable(my_main)).is_true()
assert_that(my_main()).is_equal_to("hello")
```

```python
@entrypoint
@widget
class TestWidget(Widget):
    label: QLabel = new("Test")

w = TestWidget()
assert_that(w).is_instance_of(QWidget)
assert_that(w.label.text()).is_equal_to("Test")
```
