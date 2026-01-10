# @entrypoint Decorator

## Config Storage

The decorator stores configuration on both functions and classes via the `EntryConfig` dataclass.

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

assert_that(hasattr(TestWidget, ENTRY_CONFIG_ATTR)).is_true()
config = getattr(TestWidget, ENTRY_CONFIG_ATTR)
assert_that(config.size).is_equal_to((1024, 768))
```

## No-Parens Syntax

Works with or without parentheses.

```python
@entrypoint
def my_main() -> QLabel:
    return QLabel("Hi")

assert_that(hasattr(my_main, ENTRY_CONFIG_ATTR)).is_true()
config = getattr(my_main, ENTRY_CONFIG_ATTR)
# Should have default values
assert_that(config.dark_mode).is_false()
assert_that(config.title).is_none()
```

## Preserves Original Callable

The decorator doesn't modify function/class behavior - they remain callable and instantiable.

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

## Auto-Run Detection

Entrypoint only auto-runs when `__module__ == "__main__"` AND no `QApplication` exists. In test environments (where QApp exists), it does not auto-execute.

```python
def test_entrypoint_does_not_run_when_app_exists(self, qapp: App) -> None:
    """@entrypoint should not auto-run when QApplication exists."""
    run_count = 0

    @entrypoint
    def my_main() -> QLabel:
        nonlocal run_count
        run_count += 1
        return QLabel("Hi")

    # The decorator should not have run the function
    # because QApplication already exists (via qapp fixture)
    assert_that(run_count).is_equal_to(0)
```

## QSS Stylesheet Loading

Loads `.qss` files from filesystem or QRC paths.

```python
def test_loads_qss_file(self, qapp: App, tmp_path: Path) -> None:
    """Loads and applies QSS file."""
    qss_file = tmp_path / "styles.qss"
    qss_file.write_text("QWidget { background-color: green; }")

    config = EntryConfig(stylesheet=str(qss_file))
    result = _apply_stylesheet(qapp, config)

    assert_that(result).is_none()
    assert_that(qapp.styleSheet()).contains("background-color: green")
```

```python
def test_loads_qrc_content(self) -> None:
    """Loads content from QRC path when file opens successfully."""
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
```

## SCSS Compilation

Compiles `.scss` files to CSS using SCSS compiler with search paths support.

```python
def test_compiles_scss_file(self, tmp_path: Path) -> None:
    """Compiles SCSS file to CSS string."""
    scss_file = tmp_path / "test.scss"
    scss_file.write_text("$color: blue; QWidget { background: $color; }")

    result = _compile_scss_to_string(str(scss_file), [str(tmp_path)])

    assert_that(result).contains("background")
    assert_that(result).contains("blue")
```

```python
@entrypoint(
    stylesheet="styles.scss",
    scss_search_paths=["path/to/partials", "path/to/themes"],
)
def my_main() -> QLabel:
    return QLabel("Hi")

config = getattr(my_main, ENTRY_CONFIG_ATTR)
assert_that(config.stylesheet).is_equal_to("styles.scss")
assert_that(config.scss_search_paths).is_equal_to(("path/to/partials", "path/to/themes"))
```

## Stylesheet Hot-Reload

Returns a watcher object when `watch_stylesheet=True` for filesystem QSS/SCSS files. QRC paths ignore the watch flag.

```python
def test_returns_watcher_when_watch_qss_enabled(self, qapp: App, tmp_path: Path) -> None:
    """Returns QssWatcher when watch_stylesheet=True for QSS file."""
    qss_file = tmp_path / "styles.qss"
    qss_file.write_text("QWidget { color: red; }")

    config = EntryConfig(stylesheet=str(qss_file), watch_stylesheet=True)
    watcher = _apply_stylesheet(qapp, config)

    assert_that(watcher).is_not_none()
    assert_that(type(watcher).__name__).is_equal_to("QssWatcher")
```

```python
def test_ignores_watch_for_qrc_paths(self, qapp: App) -> None:
    """watch_stylesheet is ignored for QRC paths."""
    # ... mock setup ...
    config = EntryConfig(stylesheet=":/styles/app.qss", watch_stylesheet=True)
    result = _apply_stylesheet(qapp, config)

    # Should load once and not return a watcher (can't watch QRC)
    assert_that(result).is_none()
```
