# Stylesheet Watchers

## QSS File Watching

Watch QSS files for changes and automatically apply stylesheets to widgets. Handles file creation, modification, and editor delete/recreate patterns.

```python
widget = QWidget()
qss_file = tmp_path / "styles.qss"
qss_file.write_text("QWidget { background-color: red; }")

watcher = watch_qss(widget, str(qss_file))
# Stylesheet applied immediately
assert_that(widget.styleSheet()).contains("background-color: red")
```

```python
# Watches nonexistent files and applies when created
qss_file = tmp_path / "styles.qss"
watcher = watch_qss(widget, str(qss_file))  # File doesn't exist yet
assert_that(widget.styleSheet()).is_equal_to("")

qss_file.write_text("QWidget { background-color: green; }")
# Automatically applies when file is created
```

## SCSS Compilation and Watching

Compiles SCSS to QSS with variable support, watches both main files and imported partials for changes, supports multiple search directories.

```python
scss_file = tmp_path / "styles.scss"
scss_file.write_text("$color: purple; QWidget { background-color: $color; }")
qss_file = tmp_path / "output.qss"

watcher = watch_scss(widget, str(scss_file), str(qss_file))
# Compiles and applies immediately
assert_that(widget.styleSheet()).contains("purple")
```

```python
# Watches imported SCSS files for changes
variables = partials / "_variables.scss"
variables.write_text("$bg: orange;")
scss_file.write_text("@import 'variables'; QWidget { background: $bg; }")

watcher = watch_scss(widget, str(scss_file), str(qss_file), search_paths=[str(partials)])
# Recompiles when imported file changes
```

## Convenience Function

`watch_styles()` automatically returns the appropriate watcher type based on parameters.

```python
# Returns ScssWatcher when scss_path provided
watcher = watch_styles(widget, str(qss_file), scss_path=str(scss_file))
assert_that(type(watcher).__name__).is_equal_to("ScssWatcher")

# Returns QssWatcher when no scss_path
watcher = watch_styles(widget, str(qss_file))
assert_that(type(watcher).__name__).is_equal_to("QssWatcher")
```
