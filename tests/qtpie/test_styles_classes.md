# CSS Class Helpers

## Getting and Setting Classes

Get the list of CSS classes on a widget, or set them entirely.

```python
set_classes(widget, ["foo", "bar"])
assert_that(get_classes(widget)).is_equal_to(["foo", "bar"])
```

## Adding Classes

Add one or more classes to a widget. Duplicates are ignored.

```python
add_class(widget, "foo")
add_classes(widget, ["foo", "bar"])
add_classes(widget, ["bar", "baz"])  # bar not duplicated

assert_that(get_classes(widget)).is_equal_to(["foo", "bar", "baz"])
```

## Checking Classes

Check if a widget has a specific class, or any class from a list.

```python
set_classes(widget, ["foo"])

assert_that(has_class(widget, "foo")).is_true()
assert_that(has_any_class(widget, ["bar", "foo"])).is_true()
assert_that(has_any_class(widget, ["bar", "baz"])).is_false()
```

## Removing Classes

Remove a class from a widget. No-op if not present.

```python
set_classes(widget, ["foo", "bar"])
remove_class(widget, "foo")

assert_that(get_classes(widget)).is_equal_to(["bar"])
```

## Replacing Classes

Replace one class with another, preserving position. No-op if old class not present.

```python
set_classes(widget, ["foo", "bar"])
replace_class(widget, "foo", "baz")

assert_that(get_classes(widget)).is_equal_to(["baz", "bar"])
```

## Toggling Classes

Toggle a class on/off. Adds if not present, removes if present.

```python
toggle_class(widget, "foo")  # Adds "foo"
assert_that(get_classes(widget)).contains("foo")

toggle_class(widget, "foo")  # Removes "foo"
assert_that(get_classes(widget)).does_not_contain("foo")
```
