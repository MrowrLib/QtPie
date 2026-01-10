# ObservableDict Tests

## Basic Dictionary Operations

Standard dict interface - get, set, delete, iteration, and utility methods.

```python
def test_setitem(self) -> None:
    """Set item."""
    obs = ObservableDict[str, int]()
    obs["key"] = 42
    assert_that(obs["key"]).is_equal_to(42)

def test_delitem(self) -> None:
    """Delete item."""
    obs = ObservableDict[str, int]({"a": 1, "b": 2})
    del obs["a"]
    assert_that("a" in obs).is_false()
    assert_that(len(obs)).is_equal_to(1)
```

```python
def test_update(self) -> None:
    """Update from other dict."""
    obs = ObservableDict[str, int]({"a": 1})
    obs.update({"b": 2, "c": 3})
    assert_that(obs.to_dict()).is_equal_to({"a": 1, "b": 2, "c": 3})

def test_setdefault(self) -> None:
    """Setdefault sets if missing."""
    obs = ObservableDict[str, int]({"a": 1})
    val1 = obs.setdefault("a", 99)
    val2 = obs.setdefault("b", 99)
    assert_that(val1).is_equal_to(1)
    assert_that(val2).is_equal_to(99)
    assert_that(obs["b"]).is_equal_to(99)
```

## Generic Change Callbacks

`on_change()` fires on any modification - setitem, delitem, pop, clear, update, setdefault (new keys only).

```python
def test_on_change_fires_on_setitem(self) -> None:
    """Callback fires on setitem."""
    obs = ObservableDict[str, int]()
    changes: list[str] = []
    obs.on_change(lambda: changes.append("changed"))

    obs["a"] = 1
    assert_that(changes).is_equal_to(["changed"])
```

```python
def test_on_change_not_fired_on_setdefault_existing(self) -> None:
    """Callback not fired if setdefault key exists."""
    obs = ObservableDict[str, int]({"a": 1})
    changes: list[str] = []
    obs.on_change(lambda: changes.append("changed"))

    obs.setdefault("a", 99)
    assert_that(changes).is_equal_to([])
```

## Dirty Tracking

Tracks whether dict has changed from its clean state. Becomes dirty on any modification, clean again when reverted or reset.

```python
def test_dirty_after_setitem(self) -> None:
    """Dict becomes dirty after setitem."""
    obs = ObservableDict[str, int]()
    obs["a"] = 1
    assert_that(bool(obs.is_dirty)).is_true()

def test_reset_dirty_clears(self) -> None:
    """reset_dirty marks as clean."""
    obs = ObservableDict[str, int]()
    obs["a"] = 1
    assert_that(bool(obs.is_dirty)).is_true()

    obs.reset_dirty()
    assert_that(bool(obs.is_dirty)).is_false()
```

```python
def test_clean_if_reverted_to_clean_state(self) -> None:
    """Reverting to clean state makes it clean."""
    obs = ObservableDict[str, int]({"a": 1})
    obs.reset_dirty()

    obs["b"] = 2
    assert_that(bool(obs.is_dirty)).is_true()

    del obs["b"]  # back to {"a": 1}
    assert_that(bool(obs.is_dirty)).is_false()
```

```python
def test_is_dirty_is_observable(self) -> None:
    """is_dirty can be subscribed to."""
    obs = ObservableDict[str, int]()
    dirty_states: list[bool] = []

    obs.is_dirty.on_change(lambda d: dirty_states.append(d))

    obs["a"] = 1  # clean -> dirty
    obs["b"] = 2  # stays dirty
    obs.reset_dirty()  # dirty -> clean

    assert_that(dirty_states).is_equal_to([True, False])
```

## Granular Callbacks - Insert

`on_insert(callback)` fires when adding NEW keys only (not updates). Works with `[]`, `setdefault()`, and `update()`.

```python
def test_on_insert_fires_on_new_key(self) -> None:
    """on_insert fires when adding a new key."""
    obs = ObservableDict[str, int]({"a": 1})
    inserts: list[tuple[str, int]] = []
    obs.on_insert(lambda k, v: inserts.append((k, v)))

    obs["b"] = 2
    assert_that(inserts).is_equal_to([("b", 2)])

def test_on_insert_not_fired_on_existing_key(self) -> None:
    """on_insert does NOT fire when updating existing key."""
    obs = ObservableDict[str, int]({"a": 1})
    inserts: list[tuple[str, int]] = []
    obs.on_insert(lambda k, v: inserts.append((k, v)))

    obs["a"] = 99  # update, not insert
    assert_that(inserts).is_equal_to([])
```

```python
def test_on_insert_fires_on_update_new_keys(self) -> None:
    """on_insert fires for each new key in update."""
    obs = ObservableDict[str, int]({"a": 1})
    inserts: list[tuple[str, int]] = []
    obs.on_insert(lambda k, v: inserts.append((k, v)))

    obs.update({"b": 2, "c": 3})
    assert_that(inserts).is_equal_to([("b", 2), ("c", 3)])
```

## Granular Callbacks - Replace

`on_replace(callback)` fires when updating EXISTING keys only (not new keys). Provides old and new values.

```python
def test_on_replace_fires_on_existing_key(self) -> None:
    """on_replace fires when updating existing key."""
    obs = ObservableDict[str, int]({"a": 1})
    replaces: list[tuple[str, int, int]] = []
    obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

    obs["a"] = 99
    assert_that(replaces).is_equal_to([("a", 1, 99)])

def test_on_replace_not_fired_on_new_key(self) -> None:
    """on_replace does NOT fire when adding new key."""
    obs = ObservableDict[str, int]({"a": 1})
    replaces: list[tuple[str, int, int]] = []
    obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

    obs["b"] = 2  # new key, not replace
    assert_that(replaces).is_equal_to([])
```

```python
def test_on_replace_fires_on_update_existing_keys(self) -> None:
    """on_replace fires for each existing key in update."""
    obs = ObservableDict[str, int]({"a": 1, "b": 2})
    replaces: list[tuple[str, int, int]] = []
    obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

    obs.update({"a": 10, "c": 3})  # a is replace, c is insert
    assert_that(replaces).is_equal_to([("a", 1, 10)])
```

## Granular Callbacks - Remove

`on_remove(callback)` fires on `del`, `pop()`, and `popitem()`. Not fired for `pop()` with default on missing key.

```python
def test_on_remove_fires_on_delitem(self) -> None:
    """on_remove fires on del dict[key]."""
    obs = ObservableDict[str, int]({"a": 1, "b": 2})
    removes: list[tuple[str, int]] = []
    obs.on_remove(lambda k, v: removes.append((k, v)))

    del obs["a"]
    assert_that(removes).is_equal_to([("a", 1)])

def test_on_remove_fires_on_pop(self) -> None:
    """on_remove fires on pop."""
    obs = ObservableDict[str, int]({"a": 1, "b": 2})
    removes: list[tuple[str, int]] = []
    obs.on_remove(lambda k, v: removes.append((k, v)))

    obs.pop("a")
    assert_that(removes).is_equal_to([("a", 1)])
```

```python
def test_on_remove_not_fired_on_pop_missing_with_default(self) -> None:
    """on_remove not fired on pop with default for missing key."""
    obs = ObservableDict[str, int]({"a": 1})
    removes: list[tuple[str, int]] = []
    obs.on_remove(lambda k, v: removes.append((k, v)))

    obs.pop("missing", 99)
    assert_that(removes).is_equal_to([])
```

## Granular Callbacks - Clear

`on_clear(callback)` fires on `clear()`, passing dict of all removed items (including when already empty).

```python
def test_on_clear_fires_with_removed_items(self) -> None:
    """on_clear fires with dict of all removed items."""
    obs = ObservableDict[str, int]({"a": 1, "b": 2})
    clears: list[dict[str, int]] = []
    obs.on_clear(lambda items: clears.append(items))

    obs.clear()
    assert_that(clears).is_equal_to([{"a": 1, "b": 2}])

def test_on_clear_fires_with_empty_dict_if_already_empty(self) -> None:
    """on_clear fires with empty dict if dict was already empty."""
    obs = ObservableDict[str, int]()
    clears: list[dict[str, int]] = []
    obs.on_clear(lambda items: clears.append(items))

    obs.clear()
    assert_that(clears).is_equal_to([{}])
```

## Callback Management

Multiple callbacks can be registered. Duplicate callbacks ignored. Granular and generic callbacks both fire.

```python
def test_multiple_callbacks(self) -> None:
    """Multiple callbacks all fire."""
    obs = ObservableDict[str, int]()
    results: list[int] = []
    obs.on_change(lambda: results.append(1))
    obs.on_change(lambda: results.append(2))

    obs["a"] = 1
    assert_that(results).is_equal_to([1, 2])

def test_duplicate_callback_ignored(self) -> None:
    """Same callback not added twice."""
    obs = ObservableDict[str, int]()
    results: list[int] = []

    def cb() -> None:
        results.append(1)

    obs.on_change(cb)
    obs.on_change(cb)

    obs["a"] = 1
    assert_that(results).is_equal_to([1])
```

```python
def test_granular_and_generic_both_fire(self) -> None:
    """Both granular and generic on_change fire."""
    obs = ObservableDict[str, int]()
    events: list[str] = []
    obs.on_insert(lambda k, v: events.append(f"insert:{k}={v}"))
    obs.on_change(lambda: events.append("change"))

    obs["a"] = 1
    assert_that(events).is_equal_to(["insert:a=1", "change"])
```
