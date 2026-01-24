# Auto Record Bind Feature

When a parent `Widget[T]` contains a child `Widget[T]` (same type parameter `T`), the child's record is **automatically bound** to the parent's record. This eliminates repetitive `bind="record"` declarations.

## Basic Auto-Bind

Child widgets with the same record type as parent automatically share the record.

```python
@widget(layout="vertical")
class ChildWidget(Widget[Dog]):
    name_label: QLabel = new(bind="{name}")

@widget(layout="vertical", record=Dog("Fido", 3))
class ParentWidget(Widget[Dog]):
    child: ChildWidget = new()  # Auto-binds to parent's record
```

Changes to parent's record are reflected in child:
```python
parent.record.name = "Rex"  # child.record.name also becomes "Rex"
```

## Bare Annotation Auto-Bind

Widget fields can use bare type annotations (no `new()`) - they auto-instantiate AND auto-bind.

```python
@widget(layout="vertical", record=Dog("Spot", 2))
class ParentWidget(Widget[Dog]):
    child: ChildWidget  # No new() needed - auto-creates and auto-binds
```

## Multiple Children

All children with matching type parameter auto-bind to the same record.

```python
@widget(layout="vertical", record=Dog("Buddy", 4))
class ParentWidget(Widget[Dog]):
    name_display: NameDisplay  # Both auto-bind to same record
    age_display: AgeDisplay    # Both see name="Buddy", age=4
```

## Different Types Do NOT Auto-Bind

When child has a different record type, no auto-binding occurs. Child gets its own default record.

```python
@widget(layout="vertical", record=Dog("Fido", 3))
class DogWidget(Widget[Dog]):
    cat_child: CatWidget = new()  # Widget[Cat] - gets own Cat record, not Dog
```

Plain widgets (no type parameter) are also unaffected:
```python
class PlainWidget(Widget):  # No [T]
    label: QLabel = new("Plain")
```

## Opt Out with `bind=False`

Explicitly prevent auto-binding using `bind=False`.

```python
@widget(layout="vertical", record=Dog("Fido", 3))
class ParentWidget(Widget[Dog]):
    child: ChildWidget = new(bind=False)  # Gets own default Dog record
```

## Explicit Bind Override

Explicit `bind="record"` works the same as auto-bind (redundant but valid).

```python
child: ChildWidget = new(bind="record")  # Same as auto-bind
```

## Mixed Patterns

Combine auto-bind, opt-out, and plain widgets in same parent.

```python
@widget(layout="vertical", record=Dog("Fido", 3))
class ParentWidget(Widget[Dog]):
    auto1: AutoChild              # Auto-binds (bare annotation)
    auto2: AutoChild = new()      # Auto-binds (with new())
    optout: OptOutChild = new(bind=False)  # Does NOT auto-bind
    plain: PlainChild             # No record type - unaffected
```

## Bare Field Bindings

Use `{field_name}` directly in bind expressions - automatically resolves from record.

```python
@widget(layout="vertical", record=Response(200))
class ResponseWidget(Widget[Response]):
    status: QLabel = new(bind="Code: {status_code}")  # Binds to record.status_code
```

Field bindings are reactive and update when:
- Individual field changes: `w.record.status_code = 404`
- Entire record is replaced: `w.record = Response(500)`

## Optional Fields with None

Fields can default to `None` - bindings update when values are set.

```python
@dataclass
class Response:
    status_code: int | None = None

@widget(layout="vertical")
class ResponseWidget(Widget[Response]):
    status: QLabel = new(bind="Status: {status_code}")

# Later:
w.record.status_code = 200  # Label updates automatically
```

## Format Specs

Standard Python format specs work with field bindings.

```python
time: QLabel = new(bind="Time: {time_ms:.2f} ms")  # Formats to 2 decimal places
```
