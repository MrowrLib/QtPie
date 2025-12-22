# @slot

The `@slot` decorator provides smart async/sync slot handling for Qt signal connections.

## Why @slot?

Qt's signal/slot mechanism doesn't natively support async functions. The `@slot` decorator:

- **Async functions**: Wraps with `qasync.asyncSlot` for proper event loop integration
- **Sync functions**: Optionally wraps with Qt's `@Slot` decorator
- Works with or without parentheses

## Basic Usage

### Async Slots

Use `@slot` to make async signal handlers work correctly:

```python
import asyncio
from qtpie import widget, make, slot
from qtpy.QtWidgets import QWidget, QPushButton, QLabel

@widget
class AsyncWidget(QWidget):
    button: QPushButton = make(QPushButton, "Fetch Data", clicked="fetch")
    label: QLabel = make(QLabel, "Ready")

    @slot
    async def fetch(self) -> None:
        self.label.setText("Loading...")
        await asyncio.sleep(2)  # Simulate async operation
        self.label.setText("Done!")
```

Without `@slot`, an async function connected to a Qt signal would not run properly - the coroutine would be created but never awaited.

### Sync Slots

For sync functions, `@slot` is optional but can be used for consistency:

```python
@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click", clicked="on_click")

    @slot
    def on_click(self) -> None:
        print("Clicked!")
```

For sync functions with no type arguments, `@slot` simply returns the function unchanged.

## With Type Arguments

When you need to specify signal argument types (like Qt's `@Slot(str)`), pass them to `@slot`:

```python
from qtpie import slot

@widget
class MyWidget(QWidget):
    edit: QLineEdit = make(QLineEdit, textChanged="on_text")

    @slot(str)
    async def on_text(self, text: str) -> None:
        result = await validate_async(text)
        self.update_validation(result)
```

Multiple arguments:

```python
@slot(int, str)
async def on_data(self, index: int, value: str) -> None:
    await process_async(index, value)
```

## With or Without Parentheses

Both forms work:

```python
# Without parentheses - no type args
@slot
async def on_click(self) -> None:
    await do_something()

# With empty parentheses - same as above
@slot()
async def on_click(self) -> None:
    await do_something()

# With type arguments
@slot(str)
async def on_text(self, text: str) -> None:
    await process(text)
```

## How It Works

The `@slot` decorator inspects the decorated function:

1. **If async** (`asyncio.iscoroutinefunction`):
   - Wraps with `qasync.asyncSlot(*args, **kwargs)`
   - The coroutine runs in the Qt event loop without blocking

2. **If sync**:
   - If type args provided: wraps with Qt's `@Slot(*args, **kwargs)`
   - If no args: returns the function unchanged

## Requirements

Async slots require `qasync` to be installed:

```bash
pip install qasync
```

If you try to use `@slot` on an async function without qasync, you'll get:

```
RuntimeError: qasync is required for async slots. Install it with: pip install qasync
```

QtPie's `@entry_point` and `run_app()` automatically set up qasync, so async slots work out of the box in most cases.

## Complete Example

```python
import asyncio
from qtpie import entry_point, widget, make, slot, state
from qtpy.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit

@entry_point
@widget
class SearchWidget(QWidget):
    query: str = state("")
    result: str = state("")

    search_input: QLineEdit = make(QLineEdit, bind="query")
    search_btn: QPushButton = make(QPushButton, "Search", clicked="search")
    result_label: QLabel = make(QLabel, bind="{result}")

    @slot
    async def search(self) -> None:
        if not self.query:
            self.result = "Enter a search term"
            return

        self.result = "Searching..."
        self.search_btn.setEnabled(False)

        # Simulate async API call
        await asyncio.sleep(1)
        self.result = f"Results for: {self.query}"

        self.search_btn.setEnabled(True)
```

## When to Use @slot

| Scenario | Use @slot? |
|----------|------------|
| Async signal handler | **Yes** - required |
| Sync handler needing `@Slot` type info | Yes - for type safety |
| Simple sync handler | Optional - works without it |

## See Also

- [Signals](../../basics/signals.md) - Basic signal connections
- [App & Entry Points](../../guides/app.md) - qasync setup
- [@widget](widget.md) - Async closeEvent support
- [@window](window.md) - Async closeEvent support
