# Stylesheet Watcher Tests

## QSS File Watching

Watches `.qss` files and automatically applies them to widgets when the file changes.

```python
qss_file = tmp_path / "styles.qss"
qss_file.write_text("QWidget { background-color: red; }")

watcher = watch_qss(widget, str(qss_file))

assert_that(widget.styleSheet()).contains("background-color: red")
```

Handles nonexistent files - starts watching and applies stylesheet when file is created:

```python
qss_file = tmp_path / "styles.qss"
# File doesn't exist yet

watcher = watch_qss(widget, str(qss_file))

# No stylesheet yet
assert_that(widget.styleSheet()).is_equal_to("")

# Create the file
qss_file.write_text("QWidget { background-color: green; }")

# Wait for signal
received = wait_for_signal(watcher)
assert_that(received).is_true()
assert_that(widget.styleSheet()).contains("green")
```

## SCSS Compilation and Watching

Compiles `.scss` files to `.qss` and watches for changes.

```python
scss_file = tmp_path / "styles.scss"
scss_file.write_text("$color: purple; QWidget { background-color: $color; }")
qss_file = tmp_path / "output.qss"

watcher = watch_scss(widget, str(scss_file), str(qss_file))

assert_that(qss_file.exists()).is_true()
assert_that(widget.styleSheet()).contains("purple")
```

Watches imported SCSS files and recompiles when partials change:

```python
variables = partials / "_variables.scss"
variables.write_text("$bg: orange;")

scss_file = tmp_path / "main.scss"
scss_file.write_text("@import 'variables'; QWidget { background: $bg; }")
qss_file = tmp_path / "output.qss"

watcher = watch_scss(widget, str(scss_file), str(qss_file), search_paths=[str(partials)])
assert_that(widget.styleSheet()).contains("orange")

# Change the imported file
variables.write_text("$bg: pink;")

# Wait for signal
received = wait_for_signal(watcher)
assert_that(received).is_true()
assert_that(widget.styleSheet()).contains("pink")
```

## Convenience Function

`watch_styles()` automatically chooses the right watcher based on whether `scss_path` is provided.

```python
# Returns ScssWatcher when scss_path is provided
watcher = watch_styles(widget, str(qss_file), scss_path=str(scss_file))
assert_that(type(watcher).__name__).is_equal_to("ScssWatcher")

# Returns QssWatcher when scss_path is None
watcher = watch_styles(widget, str(qss_file))
assert_that(type(watcher).__name__).is_equal_to("QssWatcher")
```
