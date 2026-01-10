# Async Support

QtPie provides seamless async/await support for signal handlers and lifecycle hooks, making it easy to perform non-blocking operations in your Qt applications.

## Overview

QtPie's async support is built on [qasync](https://github.com/CabbageDevelopment/qasync), which integrates Python's `asyncio` event loop with Qt's event loop. This allows you to use `async`/`await` syntax in your signal handlers and widget methods without blocking the UI.

**Installation:**

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

QtPie will automatically detect and use qasync when available. If qasync is not installed, attempting to use async features will raise a helpful error.

## The @slot Decorator

The `@slot` decorator is a smart wrapper that handles both async and sync functions. For async functions, it uses `qasync.asyncSlot` to ensure non-blocking execution. For sync functions, it optionally uses Qt's `@Slot` decorator for type safety.

### Basic Async Slot

```python
from qtpie import Widget, new, slot, widget
from qtpy.QtWidgets import QPushButton, QLabel
import asyncio

@widget
class AsyncExample(Widget):
    status: QLabel = new("Ready")
    button: QPushButton = new("Start Task", clicked="on_start")

    @slot
    async def on_start(self) -> None:
        self.status.setText("Working...")
        await asyncio.sleep(2)  # Simulate async work
        self.status.setText("Done!")
```

The `@slot` decorator automatically wraps the async method with `asyncSlot`, allowing the UI to remain responsive while the async operation runs.

### Async Slot with Signal Arguments

When your signal passes arguments, specify their types in the decorator:

```python
from qtpie import Widget, new, slot, widget
from qtpy.QtWidgets import QLineEdit, QLabel
import asyncio

@widget
class AsyncValidator(Widget):
    input_field: QLineEdit = new(textChanged="on_text_changed")
    result: QLabel = new("")

    @slot(str)
    async def on_text_changed(self, text: str) -> None:
        if not text:
            self.result.setText("")
            return

        self.result.setText("Validating...")
        await asyncio.sleep(0.5)  # Debounce + async validation
        is_valid = await self.validate_username(text)
        self.result.setText("Available!" if is_valid else "Taken")

    async def validate_username(self, username: str) -> bool:
        # Simulate API call
        await asyncio.sleep(0.3)
        return username not in ["admin", "root", "test"]
```

### Multiple Signal Arguments

```python
@slot(int, str)
async def on_data_received(self, index: int, value: str) -> None:
    result = await self.process_data(index, value)
    self.display_result(result)
```

### Sync Slots (Optional Type Safety)

The `@slot` decorator also works with synchronous functions. If you provide type arguments, it wraps with Qt's `@Slot` for type checking:

```python
@slot(str)
def on_text_sync(self, text: str) -> None:
    print(f"Text: {text}")

# Without type args, just returns the function as-is
@slot
def on_button_click(self) -> None:
    print("Clicked!")
```

## Async Signal Connections

You can connect async methods directly in the `new()` call:

```python
from qtpie import Widget, new, slot, widget
from qtpy.QtWidgets import QPushButton, QLabel
import asyncio

@widget
class AsyncSignals(Widget):
    status: QLabel = new("Idle")
    save_btn: QPushButton = new("Save", clicked="on_save")
    load_btn: QPushButton = new("Load", clicked="on_load")

    @slot
    async def on_save(self) -> None:
        self.status.setText("Saving...")
        await self.save_to_database()
        self.status.setText("Saved!")

    @slot
    async def on_load(self) -> None:
        self.status.setText("Loading...")
        data = await self.load_from_database()
        self.status.setText(f"Loaded: {data}")

    async def save_to_database(self) -> None:
        await asyncio.sleep(1)  # Simulate network request

    async def load_from_database(self) -> str:
        await asyncio.sleep(1)  # Simulate network request
        return "Sample data"
```

When you connect an async method by name (e.g., `clicked="on_save"`), QtPie automatically applies the `@slot` decorator if you haven't already.

## Async Lifecycle Hooks

### on_close Hook

The `on_close()` lifecycle hook allows you to perform async cleanup before a widget closes. This is particularly useful for saving state, closing connections, or confirming user actions.

```python
from qtpie import Widget, new, slot, widget
from qtpy.QtWidgets import QLabel
import asyncio

@widget
class AutoSaveWidget(Widget):
    content: QLabel = new("Unsaved changes...")

    async def on_close(self) -> None:
        """Called automatically when the widget is closing."""
        await self.save_data()
        print("Data saved before closing!")

    async def save_data(self) -> None:
        await asyncio.sleep(0.5)  # Simulate async save
```

The `@widget` decorator automatically detects async `on_close()` methods and wraps them with `qasync.asyncClose`. This ensures:

1. The async operation completes before the widget closes
2. The close event is automatically accepted after completion
3. The UI remains responsive during the operation

**Important:** You don't need to add `@slot` to `on_close()` - the `@widget` decorator handles this automatically.

### Manual closeEvent Override (Advanced)

If you need more control over the close event, you can override `closeEvent` directly. However, for async operations, using the `on_close()` hook is recommended:

```python
from qtpie import Widget, slot, widget
from qtpy.QtGui import QCloseEvent
import asyncio

@widget
class ManualCloseWidget(Widget):
    # NOT RECOMMENDED - use on_close() instead
    @slot
    async def closeEvent(self, event: QCloseEvent) -> None:
        # This won't work correctly due to type mismatch
        # closeEvent expects None return, not Coroutine
        await self.cleanup()
        event.accept()
```

The above approach has typing issues. Instead, use:

```python
@widget
class RecommendedCloseWidget(Widget):
    async def on_close(self) -> None:
        # RECOMMENDED - clean and type-safe
        await self.cleanup()
```

## Practical Examples

### Async File Upload

```python
from qtpie import Widget, Variable, new, slot, widget
from qtpy.QtWidgets import QPushButton, QProgressBar, QLabel
import asyncio

@widget
class FileUploader(Widget):
    progress_value: Variable[int] = new(0)

    progress_bar: QProgressBar = new(bind="progress_value")
    upload_btn: QPushButton = new("Upload File", clicked="on_upload")
    status: QLabel = new("Ready")

    @slot
    async def on_upload(self) -> None:
        self.upload_btn.setEnabled(False)
        self.status.setText("Uploading...")

        for i in range(101):
            self.progress_value.value = i
            await asyncio.sleep(0.02)  # Simulate upload progress

        self.status.setText("Upload complete!")
        self.upload_btn.setEnabled(True)
```

### Async Form Validation with Debouncing

```python
from qtpie import Widget, Variable, new, slot, widget
from qtpy.QtWidgets import QLineEdit, QLabel
import asyncio

@widget
class DebouncedValidator(Widget):
    email: Variable[str] = new("")

    email_input: QLineEdit = new(bind="email", textChanged="on_email_changed")
    validation_msg: QLabel = new("")

    _validation_task: asyncio.Task | None = None

    @slot(str)
    async def on_email_changed(self, text: str) -> None:
        # Cancel previous validation if still running
        if self._validation_task is not None:
            self._validation_task.cancel()

        if not text:
            self.validation_msg.setText("")
            return

        # Create new validation task with debounce
        self._validation_task = asyncio.create_task(
            self._validate_with_debounce(text)
        )

    async def _validate_with_debounce(self, email: str) -> None:
        try:
            await asyncio.sleep(0.5)  # Debounce delay
            is_valid = await self.validate_email(email)
            self.validation_msg.setText("Valid!" if is_valid else "Invalid email")
        except asyncio.CancelledError:
            pass  # Cancelled by newer input

    async def validate_email(self, email: str) -> bool:
        await asyncio.sleep(0.3)  # Simulate API call
        return "@" in email and "." in email
```

### Concurrent Async Operations

```python
from qtpie import Widget, new, slot, widget
from qtpy.QtWidgets import QPushButton, QLabel
import asyncio

@widget
class ConcurrentTasks(Widget):
    status1: QLabel = new("Task 1: Idle")
    status2: QLabel = new("Task 2: Idle")
    start_btn: QPushButton = new("Start Both Tasks", clicked="on_start")

    @slot
    async def on_start(self) -> None:
        self.start_btn.setEnabled(False)

        # Run both tasks concurrently
        await asyncio.gather(
            self.task_1(),
            self.task_2()
        )

        self.start_btn.setEnabled(True)

    async def task_1(self) -> None:
        self.status1.setText("Task 1: Running...")
        await asyncio.sleep(2)
        self.status1.setText("Task 1: Complete!")

    async def task_2(self) -> None:
        self.status2.setText("Task 2: Running...")
        await asyncio.sleep(3)
        self.status2.setText("Task 2: Complete!")
```

## Error Handling

Exceptions in async slots are handled by qasync's event loop. Always wrap async operations in try/except blocks for proper error handling:

```python
@slot
async def on_risky_operation(self) -> None:
    try:
        result = await self.might_fail()
        self.display_success(result)
    except ConnectionError as e:
        self.display_error(f"Connection failed: {e}")
    except Exception as e:
        self.display_error(f"Unexpected error: {e}")
```

## Requirements and Limitations

**Dependencies:**
- `qasync` must be installed for async support
- QtPie automatically detects qasync and uses it when available
- Without qasync, attempting to use async slots raises `RuntimeError`

**Limitations:**
- Async slots require qasync's event loop integration
- Use `@entrypoint` which sets up the event loop automatically, or manually integrate qasync with your QApplication
- Async operations don't block the UI, but long-running CPU-bound tasks should still use threads

**Best Practices:**
- Use `@slot` for all async signal handlers
- Use `on_close()` hook instead of overriding `closeEvent` for async cleanup
- Handle exceptions in async methods to prevent silent failures
- Cancel ongoing tasks when appropriate (e.g., on widget destruction)
- For CPU-intensive work, use `asyncio.to_thread()` or Qt's thread pool

## See Also

- [API Reference: @slot decorator](../reference/decorators/slot.md)
- [qasync documentation](https://github.com/CabbageDevelopment/qasync)
- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
