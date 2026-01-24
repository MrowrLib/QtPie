# MessageBox Feature Documentation

This document describes the `confirm()` and `messagebox()` functions in QtPie for displaying modal dialogs.

## confirm() Function

Simple confirmation dialog that returns a boolean.

```python
from qtpie import confirm

# Basic usage - OK/Cancel buttons
result = confirm("Are you sure?")  # Returns True for OK, False for Cancel
```

### With Custom Button Set

```python
# Yes/No buttons instead of OK/Cancel
result = confirm("Continue?", buttons=["yes", "no"])
```

### With Title

```python
confirm("Delete file?", title="Confirm Delete")
```

### With Default Button

```python
confirm("Save changes?", buttons=["ok", "cancel"], default_button="cancel")
```

## messagebox() Function

Full-featured message box that returns a `MessageBoxResult` for detailed info.

```python
from qtpie import messagebox, MessageBoxResult

result = messagebox("Save changes?", buttons=["save", "discard", "cancel"])
```

### MessageBoxResult Properties

```python
result.accepted    # True for positive buttons (ok, yes, save, etc.)
result.rejected    # True for negative buttons (cancel, no, discard, etc.)
result.button.name # Button name (e.g., "save")
result.button.text # Button display text
bool(result)       # Same as .accepted
```

## Button Customization

### List of Button Names

```python
confirm("Message", buttons=["ok", "cancel"])
```

### Dict for Custom Button Text

```python
messagebox("Continue?", buttons={"yes": "Yep!", "no": "Nope"})
```

### Available Button Names

All standard Qt buttons are supported:
- `ok`, `cancel`, `yes`, `no`
- `save`, `saveall`, `discard`, `close`
- `apply`, `reset`, `restoredefaults`, `help`
- `open`, `abort`, `retry`, `ignore`
- `yestoall`, `notoall`

### Button Name Normalization

Button names are normalized - these all work:
- `"yes_to_all"`, `"yesToAll"`, `"YES_TO_ALL"` → all become `"yestoall"`

## Icon Presets

```python
confirm("Question?", icon="question")
confirm("Warning!", icon="warning")
confirm("Error!", icon="critical")
confirm("Info", icon="information")
```

## Custom Icons

```python
from PySide6.QtGui import QIcon, QPixmap

# From resource path
confirm("Test", icon=":/icons/test.png")

# From QPixmap
pixmap = QPixmap(16, 16)
confirm("Test", icon=pixmap)

# From QIcon
icon = QIcon(QPixmap(16, 16))
confirm("Test", icon=icon)
```

## Positive vs Negative Buttons

Buttons are categorized for `result.accepted`/`result.rejected`:

**Positive (accepted=True):** `ok`, `yes`, `save`, `saveall`, `apply`, `open`, `retry`, `yestoall`

**Negative (rejected=True):** `cancel`, `no`, `discard`, `close`, `abort`, `notoall`
