# CSS Class Helpers

## Get and Set Classes

Read and write CSS classes on Qt widgets as a list.

```python
widget = QWidget()

set_classes(widget, ["foo", "bar"])

assert_that(get_classes(widget)).is_equal_to(["foo", "bar"])
```

## Add Classes

Add one or more classes without duplicates.

```python
widget = QWidget()

add_class(widget, "foo")
add_class(widget, "foo")  # No duplicate

assert_that(get_classes(widget)).is_length(1)
```

```python
add_classes(widget, ["foo", "bar"])
add_classes(widget, ["bar", "baz"])

assert_that(get_classes(widget)).is_equal_to(["foo", "bar", "baz"])
```

## Check for Classes

Check if a widget has specific classes.

```python
widget = QWidget()
set_classes(widget, ["foo"])

assert_that(has_class(widget, "foo")).is_true()
assert_that(has_class(widget, "bar")).is_false()
```

```python
assert_that(has_any_class(widget, ["bar", "foo"])).is_true()
assert_that(has_any_class(widget, ["bar", "baz"])).is_false()
```

## Remove Classes

Remove a class if present, no-op if not.

```python
widget = QWidget()
set_classes(widget, ["foo", "bar"])

remove_class(widget, "foo")

assert_that(get_classes(widget)).is_equal_to(["bar"])
```

## Replace Classes

Swap one class for another in place.

```python
widget = QWidget()
set_classes(widget, ["foo", "bar"])

replace_class(widget, "foo", "baz")

assert_that(get_classes(widget)).is_equal_to(["baz", "bar"])
```

## Toggle Classes

Add if not present, remove if present.

```python
widget = QWidget()

toggle_class(widget, "foo")  # Adds
assert_that(get_classes(widget)).contains("foo")

toggle_class(widget, "foo")  # Removes
assert_that(get_classes(widget)).does_not_contain("foo")
```
