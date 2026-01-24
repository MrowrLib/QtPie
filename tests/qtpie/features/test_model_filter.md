# Model Filter (`filter=`) Feature Documentation

The `filter=` parameter on model widgets (`QListView`, `QComboBox`, `QTableView`, `QTreeView`) enables declarative, reactive filtering of bound data.

## Basic Syntax

Filter expressions use curly braces `{}` for placeholders. Widget Variables are prefixed with `_`, item properties are accessed directly.

```python
_list: QListView = new(bind="_dogs", filter="{_search} in {name}")
```

- `{_search}` - references the widget's `_search` Variable value
- `{name}` - references each item's `name` property
- Expression evaluated per item: truthy = show, falsy = hide

---

## Supported Widget Types

Filter works on all model-based widgets:

```python
_list: QListView = new(bind="_dogs", filter="{_search} in {name}")
_combo: QComboBox = new(bind="_items", filter="{_search} in {#self}")
_table: QTableView = new(bind="_dogs", filter="{_search} in {name}")
_tree: QTreeView = new(bind="_dogs", filter="{_search} in {name}")
```

---

## Filter Expression Types

### Contains Check (string `in`)

```python
_list: QListView = new(bind="_dogs", filter="{_search} in {name}")
```

### Comparison Operators

```python
_list: QListView = new(bind="_dogs", filter="{age} >= {_min_age}")
_list: QListView = new(bind="_dogs", filter="{age} < {_max_age}")
_list: QListView = new(bind="_dogs", filter="{age} == {_target_age}")
_list: QListView = new(bind="_dogs", filter="{breed} != {_exclude_breed}")
```

### Boolean Operators (`and`, `or`, `not`)

```python
_list: QListView = new(bind="_dogs", filter="{age} >= {_min_age} and {_search} in {name}")
_list: QListView = new(bind="_dogs", filter="{name} == {_name1} or {name} == {_name2}")
_list: QListView = new(bind="_dogs", filter="not {_search} in {name}")
```

### String Methods

```python
_list: QListView = new(bind="_dogs", filter="{_search.lower()} in {name.lower()}")
_list: QListView = new(bind="_dogs", filter="{name.startswith(_prefix)}")
```

### Built-in Functions

```python
_list: QListView = new(bind="_dogs", filter="{len(name)} >= {_min_len}")
```

### Math Expressions

```python
_list: QListView = new(bind="_dogs", filter="{age} + {_bonus} >= {_threshold}")
_list: QListView = new(bind="_dogs", filter="{age} * {_factor} >= {_threshold}")
```

---

## Primitive Lists

For lists of primitives (strings, ints), use `{#self}` to reference the item value:

```python
_items: Variable[list[str]] = new(["Apple", "Banana", "Cherry"])
_list: QListView = new(bind="_items", filter="{_search} in {#self}")
```

```python
_items: Variable[list[int]] = new([1, 5, 10, 15, 20])
_list: QListView = new(bind="_items", filter="{#self} >= {_min_val}")
```

---

## Reactivity

Filters automatically re-evaluate when referenced Variables change:

```python
@widget
class Example(Widget):
    _search: Variable[str] = new("")
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
    _list: QListView = new(bind="_dogs", filter="{_search} in {name}")

# Usage:
instance._search.value = "F"  # List updates automatically to show only "Fido"
```

Filters also apply to new items added to the list:

```python
instance._dogs.append(Dog("Felix", 2))  # Automatically filtered
```

---

## Combining Filter with Format and Sort

```python
_list: QListView = new(
    bind="_dogs",
    format="{name} ({age} years)",
    filter="{age} >= {_min_age}",
    sort="{age}",
)
```

---

## Lambda Filters (Static)

Use lambda for simple static filters that don't need reactive updates:

```python
_list: QListView = new(bind="_dogs", filter=lambda x: x.age >= 3)
_list: QListView = new(bind="_dogs", filter=lambda x: "F" in x.name)
_list: QListView = new(bind="_dogs", filter=lambda x: x.breed == "labrador" and x.age > 2)
```

---

## Method Filters

Reference a widget method by name:

```python
@widget
class Example(Widget):
    _dogs: Variable[list[Dog]] = new([...])
    _list: QListView = new(bind="_dogs", filter="should_show")

    def should_show(self, dog: Dog) -> bool:
        return dog.age >= 3
```

---

## Reactive Method Filters with `filter_depends=`

Method/lambda filters don't automatically track Variable dependencies. Use `filter_depends=` to make them reactive:

```python
@widget
class Example(Widget):
    _min_age: Variable[int] = new(0)
    _dogs: Variable[list[Dog]] = new([...])
    _list: QListView = new(
        bind="_dogs",
        filter="filter_by_age",
        filter_depends=["_min_age"],  # Re-evaluate when _min_age changes
    )

    def filter_by_age(self, dog: Dog) -> bool:
        return dog.age >= self._min_age.value
```

Multiple dependencies:

```python
_list: QListView = new(
    bind="_dogs",
    filter="complex_filter",
    filter_depends=["_min_age", "_search"],
)
```

---

## Typical Search Pattern

```python
@widget
class SearchableList(Widget):
    _search: Variable[str] = new("")
    _items: Variable[list[Dog]] = new([...])
    _list: QListView = new(
        bind="_items",
        filter="search_filter",
        filter_depends=["_search"],
    )

    def search_filter(self, dog: Dog) -> bool:
        search = self._search.value.lower()
        if not search:
            return True
        return search in dog.name.lower()
```

---

## Summary of Filter Approaches

| Approach | Reactive | Use Case |
|----------|----------|----------|
| Expression `filter="{_var} in {name}"` | Yes (automatic) | Most common, recommended |
| Lambda `filter=lambda x: x.age >= 3` | No | Static filters |
| Method `filter="method_name"` | No | Complex logic, no reactivity needed |
| Method + depends `filter="method", filter_depends=["_var"]` | Yes (manual) | Complex logic with reactivity |
