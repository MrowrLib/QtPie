# App Class Tests

## App is QApplication

The `App` class extends `QApplication`, providing QtPie's custom application class.

```python
def test_app_is_qapplication(self, qapp: App) -> None:
    """App should be a QApplication instance."""
    assert_that(qapp).is_instance_of(QApplication)

def test_app_is_our_app_class(self, qapp: App) -> None:
    """qapp fixture should use our App class."""
    assert_that(qapp).is_instance_of(App)
```

## App.run and App.run_async

The `App` class provides `run()` and `run_async()` methods for starting the event loop.

```python
def test_app_has_run_method(self, qapp: App) -> None:
    """App should have a run method."""
    assert_that(qapp.run).is_not_none()
    assert_that(callable(qapp.run)).is_true()

def test_app_has_run_async_method(self, qapp: App) -> None:
    """App should have a run_async method."""
    assert_that(qapp.run_async).is_not_none()
    assert_that(callable(qapp.run_async)).is_true()
```

## App.load_stylesheet

Load QSS stylesheets from file paths.

```python
def test_app_load_stylesheet_from_file(self, qapp: App, tmp_path: Path) -> None:
    """App should be able to load a stylesheet from a file."""
    qss_file = tmp_path / "test.qss"
    qss_file.write_text("QWidget { background-color: red; }")

    qapp.load_stylesheet(str(qss_file))

    assert_that(qapp.styleSheet()).contains("background-color")
```

## Dark/Light Mode

Toggle between dark and light mode themes.

```python
def test_app_has_dark_light_mode_methods(self, qapp: App) -> None:
    """App should have enable_dark_mode and enable_light_mode methods."""
    assert_that(callable(qapp.enable_dark_mode)).is_true()
    assert_that(callable(qapp.enable_light_mode)).is_true()
```

## Lifecycle Hooks

The `App` class supports the `__setup__()` lifecycle hook for customization.

```python
def test_setup_hook_called_on_subclass(self) -> None:
    """__setup__() hook should be called when overridden in subclass."""
    setup_called = False

    class MyApp(App):
        @override
        def __setup__(self) -> None:
            nonlocal setup_called
            setup_called = True

    assert_that(hasattr(MyApp, "__setup__")).is_true()
```

## run_app Function

Standalone `run_app()` function accepts any `QApplication` instance.

```python
def test_run_app_accepts_qapplication(self) -> None:
    """run_app should accept any QApplication."""
    from qtpie import run_app

    sig = inspect.signature(run_app)
    params = list(sig.parameters.keys())
    assert_that(params).contains("app")
```
