# Dirty Tracking

Track which fields have been modified in your `Widget[T]` forms. Perfect for implementing "unsaved changes" warnings and conditional saves.

---

## Quick Example

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QWidget, QLineEdit, QPushButton, QLabel

@dataclass
class User:
    name: str = ""
    email: str = ""

@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)
    save: QPushButton = make(QPushButton, "Save", clicked="on_save")
    status: QLabel = make(QLabel)

    def setup(self) -> None:
        # Update status when fields change
        self.name.textChanged.connect(self.update_status)
        self.email.textChanged.connect(self.update_status)

    def update_status(self) -> None:
        if self.is_dirty():
            self.status.setText(f"Modified: {', '.join(self.dirty_fields())}")
        else:
            self.status.setText("No changes")

    def on_save(self) -> None:
        self.save_to(self.model)
        self.reset_dirty()  # Mark as clean after save
        self.status.setText("Saved!")
```

---

## The Three Methods

### `is_dirty()` - Has Anything Changed?

Returns `True` if any field has been modified since the widget was created (or since the last `reset_dirty()`).

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)

w = UserEditor()
print(w.is_dirty())  # False - nothing changed yet

w.name.setText("Alice")
print(w.is_dirty())  # True - name was modified
```

**Use cases:**
- Enable/disable "Save" button
- Show "unsaved changes" indicator
- Prompt before closing window

### `dirty_fields()` - Which Fields Changed?

Returns a `set[str]` of field names that have been modified.

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)

w = UserEditor()
w.name.setText("Bob")

print(w.dirty_fields())  # {'name'}

w.email.setText("bob@example.com")
print(w.dirty_fields())  # {'name', 'email'}
```

**Use cases:**
- Show which fields need saving
- Highlight modified fields in UI
- Build change summaries

### `reset_dirty()` - Mark Current State as Clean

Resets the dirty tracking, making the current values the new baseline.

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)

w = UserEditor()
w.name.setText("Alice")
print(w.is_dirty())  # True

w.reset_dirty()
print(w.is_dirty())  # False - current state is now "clean"

w.name.setText("Bob")
print(w.is_dirty())  # True - changed from the new baseline
```

**Use cases:**
- After saving to model/database
- After loading new data
- After user confirms discard

---

## Common Patterns

### Unsaved Changes Warning

```python
@widget
class DocumentEditor(QWidget, Widget[Document]):
    title: QLineEdit = make(QLineEdit)
    content: QTextEdit = make(QTextEdit)

    def closeEvent(self, event) -> None:
        if self.is_dirty():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Close anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()
```

### Conditional Save Button

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)
    save: QPushButton = make(QPushButton, "Save", clicked="on_save")

    def setup(self) -> None:
        # Disable save button when nothing changed
        self.name.textChanged.connect(self.update_save_button)
        self.email.textChanged.connect(self.update_save_button)
        self.update_save_button()

    def update_save_button(self) -> None:
        self.save.setEnabled(self.is_dirty())

    def on_save(self) -> None:
        self.save_to(self.model)
        self.reset_dirty()
        self.update_save_button()
```

### Show Modified Fields

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)
    status: QLabel = make(QLabel)

    def setup(self) -> None:
        self.name.textChanged.connect(self.show_changes)
        self.email.textChanged.connect(self.show_changes)

    def show_changes(self) -> None:
        if not self.is_dirty():
            self.status.setText("No changes")
            return

        fields = self.dirty_fields()
        self.status.setText(f"Modified: {', '.join(sorted(fields))}")
```

---

## How It Works

Dirty tracking is powered by [Observant](https://mrowrlib.github.io/observant.py/)'s [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/) ([PyPI](https://pypi.org/project/observant/)):

1. When you create a `Widget[T]`, QtPie wraps your model in an `ObservableProxy`
2. The proxy tracks the **initial value** of each field
3. When a field changes, the proxy compares the new value to the initial value
4. `reset_dirty()` updates the baseline to the current values

**Important:** Dirty tracking is always enabled for `Widget[T]`. No special configuration needed.

---

## Combined with Save/Load

Dirty tracking works beautifully with save/load operations:

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)

    save: QPushButton = make(QPushButton, "Save", clicked="on_save")
    cancel: QPushButton = make(QPushButton, "Cancel", clicked="on_cancel")

    def on_save(self) -> None:
        # Save proxy values to model
        self.save_to(self.model)

        # Mark as clean - nothing dirty anymore
        self.reset_dirty()

        # TODO: Save model to database...
        self.close()

    def on_cancel(self) -> None:
        if self.is_dirty():
            reply = QMessageBox.question(
                self,
                "Discard Changes?",
                f"Discard changes to {', '.join(self.dirty_fields())}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.close()
```

---

## See Also

- [Record Widgets](record-widgets.md) - Learn about `Widget[T]` and the proxy
- [Save & Load](save-load.md) - Persist changes to models
- [Validation](validation.md) - Validate before saving
- [Observant Integration](../guides/observant.md) - Understanding the reactive layer
