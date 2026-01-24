# Model Sort Feature

The `sort=` parameter on model widgets (QListView, QComboBox, QTableView, QTreeView) enables declarative sorting of bound data.

## Sort Syntax Options

Three ways to specify sort behavior:

| Syntax | Example | Description |
|--------|---------|-------------|
| Expression string | `sort="{age}"` | Sort by expression result |
| Method name | `sort="get_sort_key"` | Call widget method |
| Lambda/Callable | `sort=lambda x: x.age` | Direct callable |

## Sort by Expression String

Use curly braces with attribute access or expressions.

### Sort by Attribute

```python
_list: QListView = new(bind="_dogs", sort="{age}")       # int attribute
_list: QListView = new(bind="_dogs", sort="{name}")      # string attribute
_list: QListView = new(bind="_people", sort="{score}")   # float attribute
```

### Sort Descending (Numeric)

Negate the value for descending order:

```python
_list: QListView = new(bind="_dogs", sort="{-age}")
```

### Sort by Computed Expression

```python
_list: QListView = new(bind="_dogs", sort="{len(name)}")
```

### Sort by Multiple Columns (Tuple)

Use tuple expression for primary/secondary sort:

```python
# Sort by age, then by name
_list: QListView = new(bind="_dogs", sort="{(age, name)}")

# Sort by grade asc, score desc
_list: QListView = new(bind="_students", sort="{(grade, -score)}")
```

### Sort Primitives with #self

For lists of primitives (strings, ints), use `{#self}`:

```python
_items: Variable[list[str]] = new(["Zebra", "Apple", "Mango"])
_list: QListView = new(bind="_items", sort="{#self}")
```

## Sort by Lambda

Direct callable for full control:

```python
# Simple attribute
_list: QListView = new(bind="_dogs", sort=lambda x: x.age)

# Descending
_list: QListView = new(bind="_dogs", sort=lambda x: -x.age)

# Tuple for multi-column
_list: QListView = new(bind="_dogs", sort=lambda x: (x.age, x.name))
```

## Sort by Method Name

Reference a widget method by string name:

```python
_list: QListView = new(bind="_dogs", sort="get_sort_key")

def get_sort_key(self, dog: Dog) -> int:
    return dog.age
```

## Combining Sort and Filter

Both `sort=` and `filter=` can be used together:

```python
_min_age: Variable[int] = new(0)
_dogs: Variable[list[Dog]] = new([...])
_list: QListView = new(
    bind="_dogs",
    filter="{age} >= {_min_age}",
    sort="{age}",
)
```

The filter is applied first, then sorting on the filtered results.

## Supported Widget Types

The sort feature works on all model-based widgets:

- `QListView`
- `QComboBox`
- `QTableView`
- `QTreeView`

```python
_combo: QComboBox = new(bind="_items", sort="{#self}")
_table: QTableView = new(bind="_dogs", sort="{age}")
_tree: QTreeView = new(bind="_dogs", sort="{(age, name)}")
```
