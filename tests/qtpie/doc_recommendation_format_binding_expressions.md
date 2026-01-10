# Documentation Proposal: Format Binding Expressions

## Priority
**HIGH** - This is a core feature of QtPie's reactive system and differentiates it from other Qt frameworks.

## Files to Add/Update

### New File
- `docs/state/format-expressions.md` - Primary documentation page for format binding expressions

### Updates Required
- `docs/state/bindings.md` - Create this as the parent/overview page, with a section linking to format-expressions
- `docs/index.md` - Add a bullet point in "Reactive State" section highlighting advanced expressions
- `docs/start/concepts.md` - Create this with a brief mention of format expressions as an advanced binding feature

## Suggested Nav Location

Already exists in mkdocs.yml at the correct location:
```yaml
- Reactive State:
    - Variables: state/variables.md
    - Bindings: state/bindings.md
    - Format Expressions: state/format-expressions.md  # ← This page
    - Property Bindings: state/property-bindings.md
```

This is the ideal placement - between basic bindings and property bindings.

## Content Outline

### `docs/state/format-expressions.md`

1. **Introduction** (2-3 paragraphs)
   - What are format expressions?
   - Why use them vs simple variable references?
   - Brief comparison: `bind="_name"` vs `bind="Hello, {_name}!"` vs `bind="{_name.upper()}"`

2. **Basic Expressions**
   - String interpolation with multiple variables
   - Builtin functions: `len()`, `str()`, `int()`, `abs()`, `min()`, `max()`, `round()`
   - String methods: `upper()`, `lower()`, `title()`, `strip()`, `replace()`
   - Method chaining: `_name.strip().lower()`

3. **Math Expressions**
   - Basic operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`
   - Complex expressions with parentheses: `{(_x + _y) * _z}`
   - Multiple variables in one expression

4. **Format Specifications**
   - Float precision: `{_price:.2f}`
   - Percentage: `{_ratio:.1%}`
   - Padding/alignment
   - Combining with expressions: `${_price * 1.1:.2f}`

5. **Special Placeholders**
   - Table of all placeholders (from CLAUDE.md)
   - When to use each one
   - Context-dependent behavior

6. **Instance Methods**
   - Calling widget methods from bindings
   - Methods with parameters
   - Accessing widget properties

7. **Special Contexts**
   - `Variable[T, W]` binding context (`#self`, `#var`, `#widget`)
   - List repeater context (`#index`, `#self`)
   - Dict repeater context (`#key`, `#value`, `#self`)
   - Record widget context (direct property access)

8. **Reactivity**
   - How dependency tracking works
   - Automatic re-evaluation on variable changes
   - Multiple dependencies in one expression

9. **Error Handling**
   - What happens on exceptions (shows error message)
   - Division by zero, None values, etc.
   - Best practices for safe expressions

10. **Advanced Patterns**
    - Conditional expressions (if available)
    - Nested method calls
    - Complex data transformations

11. **Performance Considerations**
    - Keep expressions simple
    - Avoid expensive operations
    - When to use computed properties instead

12. **Troubleshooting**
    - Common errors and solutions
    - Debugging expressions
    - Syntax limitations

## Code Examples Needed

### Basic String Interpolation
```python
@widget
class Greeter(Widget):
    _first: Variable[str] = new("John")
    _last: Variable[str] = new("Doe")
    _greeting: QLabel = new(bind="Hello, {_first} {_last}!")
```

### Builtin Functions
```python
@widget
class StringInfo(Widget):
    _text: Variable[str] = new("Hello")
    _length: QLabel = new(bind="Length: {len(_text)}")
    _upper: QLabel = new(bind="Upper: {_text.upper()}")
```

### Math Expressions
```python
@widget
class Calculator(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(5)
    _sum: QLabel = new(bind="Sum: {_x + _y}")
    _product: QLabel = new(bind="Product: {_x * _y}")
    _complex: QLabel = new(bind="(x+y)*2 = {(_x + _y) * 2}")
```

### Format Specs
```python
@widget
class PriceDisplay(Widget):
    _price: Variable[float] = new(19.99)
    _tax_rate: Variable[float] = new(0.1)
    _label: QLabel = new(bind="Total: ${_price * (1 + _tax_rate):.2f}")
```

### Instance Methods
```python
@widget
class CustomFormatter(Widget):
    _count: Variable[int] = new(5)
    _label: QLabel = new(bind="{pluralize('item', _count)}")

    def pluralize(self, word: str, count: int) -> str:
        return f"{count} {word}{'s' if count != 1 else ''}"
```

### Variable[T, W] Context
```python
@widget
class Example(Widget):
    _name: Variable[str, QLabel] = new("hello")(
        bind="Upper: {#self.upper()}, Length: {len(#var)}"
    )
```

### List Repeater Context
```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])
    _labels: list[QLabel] = new(
        bind="_items",
        format="Item #{#index}: {#self.upper()}"
    )
```

### Dict Repeater Context
```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
    _labels: list[QLabel] = new(
        bind="_scores",
        format="{#key} scored {#value} points"
    )
```

### Record Widget
```python
@dataclass
class Person:
    first_name: str
    last_name: str
    age: int

@widget(record=Person("Alice", "Smith", 30))
class PersonDisplay(Widget[Person]):
    _greeting: QLabel = new(bind="Hello, {first_name} {last_name}!")
    _age_info: QLabel = new(bind="You are {age} years old")
```

### Reactivity Example
```python
@widget
class ReactiveCalculator(Widget):
    _price: Variable[float] = new(100.0)
    _discount: Variable[float] = new(0.1)
    _quantity: Variable[int] = new(1)

    _subtotal: QLabel = new(bind="Subtotal: ${_price * _quantity:.2f}")
    _discount_amount: QLabel = new(bind="Discount: -${_price * _quantity * _discount:.2f}")
    _total: QLabel = new(bind="Total: ${_price * _quantity * (1 - _discount):.2f}")
```

### Error Handling
```python
@widget
class SafeDivision(Widget):
    _numerator: Variable[int] = new(10)
    _denominator: Variable[int] = new(0)
    # Division by zero shows error message instead of crashing
    _result: QLabel = new(bind="{_numerator / _denominator}")
```

## Cross-References

### Internal Links
- [Variables](variables.md) - Understanding Variable[T]
- [Bindings](bindings.md) - Simple variable bindings (parent page)
- [Property Bindings](property-bindings.md) - Using expressions in visible=, enabled=
- [Lists & Dicts](../data/lists-dicts.md) - List/dict repeater placeholders
- [Record Widgets](../data/records.md) - Direct property access in Widget[T]
- [Variable Reference](../reference/classes/variable.md) - Variable[T] and Variable[T, W]

### External Links
- Python string formatting documentation (for format specs)
- Python built-in functions documentation

### Related Features
- Mention that `enabled=` and `visible=` also support expressions (link to property-bindings.md)
- Mention that decorator kwargs support expressions (e.g., `@widget(windowTitle="{_title}")`)
- Note that translatable strings `t()` can be used in expressions

## Success Metrics

This documentation should enable users to:

1. **Understand** when to use format expressions vs simple bindings
2. **Write** expressions using builtins, methods, and math operators
3. **Use** special placeholders (`#self`, `#index`, etc.) correctly in different contexts
4. **Debug** expression errors effectively
5. **Combine** multiple variables and transformations in one expression
6. **Apply** format specifications for number formatting
7. **Call** instance methods from bindings for custom formatting

## Notes

- This feature is already implemented and tested (see `test_format_binding_expressions.md`)
- The test file shows comprehensive coverage of the feature
- Documentation should match the maturity level of the implementation
- Emphasize that this is a "power user" feature - simple `bind="_var"` is often sufficient
- Include a "When to Use" callout box early in the doc
- Add warning about expression complexity and maintainability
- Consider adding a comparison table: "Simple Binding vs Format Expression vs Computed Property"
