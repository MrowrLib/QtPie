# @slot

Smart decorator for Qt signal handlers that supports both async and sync functions.

## Signature

```python
def slot[F: Callable[..., object]](
    *args: object,
    **kwargs: object
) -> Callable[[F], F] | F
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `*args` | `object` | Type arguments for Qt signal (e.g., `str`, `int`, `bool`) |
| `**kwargs` | `object` | Additional keyword arguments passed to the underlying `Slot` decorator |

## Return Value

Returns the decorated function. For async functions, wraps with `qasync.asyncSlot`. For sync functions with type arguments, wraps with Qt's `@Slot`.

## Description

The `@slot` decorator is a unified interface for creating Qt slots that works with both synchronous and asynchronous functions.

**For async functions:**
- Automatically uses `qasync.asyncSlot` for non-blocking execution
- Requires `qasync` to be installed
- Raises `RuntimeError` if qasync is not available

**For sync functions:**
- Uses Qt's `@Slot` decorator if type arguments are provided
- Returns the function as-is if no type arguments (no overhead)

## Usage

### Basic Syntax

```python
from qtpie import slot

# Without parentheses (no signal arguments)
@slot
async def on_click(self) -> None:
    await asyncio.sleep(1)
    print("Done!")

# With parentheses (for type safety)
@slot()
async def on_action(self) -> None:
    await self.perform_action()

# With signal type arguments
@slot(str)
async def on_text_changed(self, text: str) -> None:
    result = await self.validate(text)
```

### Async Slots

```python
from qtpie import Widget, new, slot, widget
from qtpy.QtWidgets import QPushButton, QLabel
import asyncio

@widget
class AsyncWidget(Widget):
    button: QPushButton = new("Click Me", clicked="on_click")
    status: QLabel = new("Ready")

    @slot
    async def on_click(self) -> None:
        self.status.setText("Processing...")
        await asyncio.sleep(2)
        self.status.setText("Complete!")
```

### Async Slots with Signal Arguments

Specify the signal's argument types in the decorator:

```python
@widget
class TextHandler(Widget):
    input_field: QLineEdit = new(textChanged="on_text")

    @slot(str)
    async def on_text(self, text: str) -> None:
        result = await self.process_text(text)
        self.display_result(result)
```

### Multiple Arguments

```python
@slot(int, str)
async def on_data(self, index: int, value: str) -> None:
    await self.handle_data(index, value)

@slot(bool, int, str)
async def on_complex_signal(self, flag: bool, count: int, name: str) -> None:
    await self.process(flag, count, name)
```

### Sync Slots

The decorator also works with synchronous functions:

```python
# With type safety
@slot(str)
def on_text_sync(self, text: str) -> None:
    print(f"Received: {text}")

# Without type arguments (no overhead)
@slot
def on_button(self) -> None:
    print("Clicked!")
```

## Integration with QtPie

### Signal Connections by Name

When using `new()` with signal connections, the `@slot` decorator is recommended but not strictly required for async methods:

```python
@widget
class MyWidget(Widget):
    # Connection by name - decorator applied automatically if needed
    button: QPushButton = new("Save", clicked="on_save")

    # Explicit @slot decorator (recommended for clarity)
    @slot
    async def on_save(self) -> None:
        await self.save_data()
```

### Lambda Connections

For lambda or inline connections, ensure async functions are wrapped:

```python
from qasync import asyncSlot

@widget
class MyWidget(Widget):
    # Lambda with async - wrap explicitly
    button: QPushButton = new(
        "Process",
        clicked=asyncSlot(lambda: asyncio.create_task(self.process()))
    )
```

However, for clarity and maintainability, named methods with `@slot` are preferred.

## Error Handling

Exceptions in async slots are propagated through qasync's event loop. Always handle exceptions appropriately:

```python
@slot
async def on_operation(self) -> None:
    try:
        await self.risky_operation()
    except ValueError as e:
        self.show_error(f"Invalid value: {e}")
    except Exception as e:
        self.show_error(f"Error: {e}")
```

## Type Safety

The `@slot` decorator preserves type information:

```python
from typing import override

@widget
class MyWidget(Widget):
    # Type checker knows the signature
    @slot(str, int)
    async def on_custom_signal(self, name: str, count: int) -> None:
        await self.process(name, count)
```

## Requirements

**For async support:**

- `qasync` must be installed:

    === "uv"

        ```bash
        uv add qasync
        ```

    === "poetry"

        ```bash
        poetry add qasync
        ```

    === "pip"

        ```bash
        pip install qasync
        ```

- Your application must use qasync's event loop (automatic with `@entrypoint`)

**For sync slots:**
- No additional dependencies
- Qt's `Slot` decorator is used only when type arguments are provided

## Comparison with Qt's @Slot

| Feature | `@slot` (QtPie) | `@Slot` (Qt) |
|---------|-----------------|--------------|
| Async support | Yes (with qasync) | No |
| Type arguments | Optional | Optional |
| Auto-detection | Yes (async vs sync) | No |
| Overhead when unused | None | None |
| Return type preservation | Yes | Yes |

## Common Patterns

### Debounced Async Validation

```python
@widget
class ValidatedInput(Widget):
    _task: asyncio.Task | None = None

    @slot(str)
    async def on_input_changed(self, text: str) -> None:
        if self._task:
            self._task.cancel()

        self._task = asyncio.create_task(self._validate(text))

    async def _validate(self, text: str) -> None:
        await asyncio.sleep(0.3)  # Debounce
        is_valid = await self.check_validity(text)
        self.update_ui(is_valid)
```

### Sequential Async Operations

```python
@slot
async def on_submit(self) -> None:
    self.set_busy(True)
    try:
        await self.validate_form()
        await self.save_to_database()
        await self.send_confirmation()
        self.show_success()
    except Exception as e:
        self.show_error(str(e))
    finally:
        self.set_busy(False)
```

### Parallel Async Operations

```python
@slot
async def on_load_all(self) -> None:
    results = await asyncio.gather(
        self.load_users(),
        self.load_settings(),
        self.load_preferences(),
        return_exceptions=True
    )
    self.handle_results(results)
```

## Notes

- The `@slot` decorator can be used with or without parentheses when no arguments are needed
- For async functions, qasync must be installed or `RuntimeError` is raised
- Type arguments are passed directly to the underlying `@Slot` or `asyncSlot` decorator
- The decorator preserves the original function's signature and return type for type checkers

## See Also

- [Async Support Guide](../../guides/async.md)
- [qasync.asyncSlot documentation](https://github.com/CabbageDevelopment/qasync)
- [Qt Slot documentation](https://doc.qt.io/qtforpython/overviews/signalsandslots.html)
