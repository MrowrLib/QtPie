# Async Support

QtPie has built-in async/await support. No setup required.

---

## Quick Start

Use `@slot` on async signal handlers:

```python
import asyncio
from qtpie import entrypoint, widget, make, slot
from qtpy.QtWidgets import QWidget, QPushButton, QLabel

@entrypoint
@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Fetch", clicked="fetch")
    label: QLabel = make(QLabel, "Ready")

    @slot
    async def fetch(self) -> None:
        self.label.setText("Loading...")
        await asyncio.sleep(1)
        self.label.setText("Done!")
```

That's it. The `@entrypoint` decorator sets up the async event loop automatically.

---

## Async Signal Handlers with @slot

The `@slot` decorator makes async functions work as Qt signal handlers.

### Basic Usage

```python
@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click", clicked="on_click")

    @slot
    async def on_click(self) -> None:
        await asyncio.sleep(1)
        print("Clicked!")
```

Without `@slot`, the coroutine would be created but never awaited.

### With Signal Arguments

Pass type arguments to `@slot` when your handler receives signal arguments:

```python
@widget
class MyWidget(QWidget):
    edit: QLineEdit = make(QLineEdit, textChanged="on_text")

    @slot(str)
    async def on_text(self, text: str) -> None:
        result = await validate_async(text)
        self.show_validation(result)
```

Multiple arguments:

```python
@slot(int, str)
async def on_data(self, index: int, value: str) -> None:
    await process_async(index, value)
```

### Concurrent Execution

Async handlers run concurrently. Clicking multiple buttons fires all handlers without blocking:

```python
@widget
class MyWidget(QWidget):
    btn1: QPushButton = make(QPushButton, "Task 1", clicked="task_one")
    btn2: QPushButton = make(QPushButton, "Task 2", clicked="task_two")

    @slot
    async def task_one(self) -> None:
        print("Task 1 started")
        await asyncio.sleep(2)
        print("Task 1 done")

    @slot
    async def task_two(self) -> None:
        print("Task 2 started")
        await asyncio.sleep(1)
        print("Task 2 done")
```

Clicking both buttons quickly prints:
```
Task 1 started
Task 2 started
Task 2 done
Task 1 done
```

### Sync Functions

For sync functions, `@slot` is optional. It passes through unchanged unless you provide type arguments:

```python
@slot
def on_click(self) -> None:
    print("Works fine")

@slot(str)
def on_text(self, text: str) -> None:
    # Wrapped with Qt's @Slot(str) for type safety
    print(f"Text: {text}")
```

---

## Async closeEvent

Write `async def closeEvent` directly in `@widget` or `@window` classes. It's automatically wrapped:

```python
@widget
class MyWidget(QWidget):
    async def closeEvent(self, event) -> None:
        await self.save_data()
        await self.disconnect_services()
        print("Cleanup complete")
```

### Fire-and-Forget vs Wait-for-Completion

There's an important difference:

| Method | Behavior |
|--------|----------|
| `@slot` handlers | **Fire-and-forget** - returns immediately, coroutine runs on event loop |
| `async closeEvent` | **Waits for completion** - spins event loop until coroutine finishes |

Both keep the UI responsive. The difference is whether the function returns immediately or waits for the async work to complete.

This matters for `closeEvent` - cleanup must finish before the widget is destroyed.

### Example: Save Before Close

```python
@widget
class EditorWidget(QWidget):
    content: QTextEdit = make(QTextEdit)

    async def closeEvent(self, event) -> None:
        if self.has_unsaved_changes():
            await self.auto_save()
        # Window closes after save completes
```

---

## How It Works

You don't need to understand this to use async in QtPie, but here's what happens:

1. **`@entrypoint`** (or `run_app()` / `App.run()`) sets up a `qasync.QEventLoop`
2. **`@slot`** wraps async functions with `qasync.asyncSlot` - calls `asyncio.ensure_future()` and returns the task immediately
3. **`async closeEvent`** is auto-wrapped with `qasync.asyncClose` - spins in a loop calling `processEvents()` until the coroutine completes

The qasync library bridges Qt's event loop with Python's asyncio, letting them work together.

---

## Complete Example

A search widget with async API calls:

```python
import asyncio
from qtpie import entrypoint, widget, make, slot, state
from qtpy.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit

@entrypoint
@widget
class SearchWidget(QWidget):
    query: str = state("")
    result: str = state("")

    search_input: QLineEdit = make(QLineEdit, bind="query", placeholderText="Search...")
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

    async def closeEvent(self, event) -> None:
        # Save search history before closing
        await self.save_history()
```

---

## See Also

- [@slot Reference](../reference/decorators/slot.md) - Full decorator API
- [Signals](../basics/signals.md) - Basic signal connections
- [App & Entry Points](app.md) - Event loop setup details
