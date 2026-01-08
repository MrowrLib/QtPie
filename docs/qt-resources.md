# Qt Resources

QtPie builds on Qt/PySide6. This page provides links to essential Qt documentation and resources for when you need to go deeper.

## Official Qt Documentation

### PySide6 (Recommended)

- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/) - Official Python bindings documentation
- [PySide6 API Reference](https://doc.qt.io/qtforpython-6/api.html) - Complete API reference
- [PySide6 Examples](https://doc.qt.io/qtforpython-6/examples/index.html) - Official examples

### Qt 6 (C++ Reference)

- [Qt 6 Documentation](https://doc.qt.io/qt-6/) - Main Qt documentation
- [Qt Widgets](https://doc.qt.io/qt-6/qtwidgets-index.html) - Widget classes reference
- [Qt Style Sheets](https://doc.qt.io/qt-6/stylesheet.html) - Complete QSS reference

## Commonly Used Widgets

### Input Widgets

| Widget | Description | Common Properties |
|--------|-------------|-------------------|
| [QLineEdit](https://doc.qt.io/qt-6/qlineedit.html) | Single-line text input | `text`, `placeholderText`, `echoMode` |
| [QTextEdit](https://doc.qt.io/qt-6/qtextedit.html) | Multi-line text editor | `plainText`, `html` |
| [QSpinBox](https://doc.qt.io/qt-6/qspinbox.html) | Integer spinner | `value`, `minimum`, `maximum` |
| [QDoubleSpinBox](https://doc.qt.io/qt-6/qdoublespinbox.html) | Float spinner | `value`, `decimals` |
| [QCheckBox](https://doc.qt.io/qt-6/qcheckbox.html) | Checkbox | `checked`, `tristate` |
| [QRadioButton](https://doc.qt.io/qt-6/qradiobutton.html) | Radio button | `checked` |
| [QComboBox](https://doc.qt.io/qt-6/qcombobox.html) | Dropdown selector | `currentText`, `currentIndex` |
| [QSlider](https://doc.qt.io/qt-6/qslider.html) | Slider control | `value`, `minimum`, `maximum` |

### Display Widgets

| Widget | Description | Common Properties |
|--------|-------------|-------------------|
| [QLabel](https://doc.qt.io/qt-6/qlabel.html) | Text/image display | `text`, `pixmap` |
| [QProgressBar](https://doc.qt.io/qt-6/qprogressbar.html) | Progress indicator | `value`, `minimum`, `maximum` |
| [QLCDNumber](https://doc.qt.io/qt-6/qlcdnumber.html) | LCD-style display | `value`, `digitCount` |

### Container Widgets

| Widget | Description | Notes |
|--------|-------------|-------|
| [QWidget](https://doc.qt.io/qt-6/qwidget.html) | Base container | Use with layouts |
| [QGroupBox](https://doc.qt.io/qt-6/qgroupbox.html) | Labeled group | `title` property |
| [QScrollArea](https://doc.qt.io/qt-6/qscrollarea.html) | Scrollable container | Set widget with `setWidget()` |
| [QTabWidget](https://doc.qt.io/qt-6/qtabwidget.html) | Tabbed pages | Use `addTab()` |
| [QStackedWidget](https://doc.qt.io/qt-6/qstackedwidget.html) | Stacked pages | `currentIndex` |

### Button Widgets

| Widget | Description | Common Signals |
|--------|-------------|----------------|
| [QPushButton](https://doc.qt.io/qt-6/qpushbutton.html) | Standard button | `clicked`, `pressed`, `released` |
| [QToolButton](https://doc.qt.io/qt-6/qtoolbutton.html) | Toolbar button | `clicked`, `triggered` |

## Layouts

| Layout | Description | Qt Docs |
|--------|-------------|---------|
| QVBoxLayout | Vertical arrangement | [Reference](https://doc.qt.io/qt-6/qvboxlayout.html) |
| QHBoxLayout | Horizontal arrangement | [Reference](https://doc.qt.io/qt-6/qhboxlayout.html) |
| QFormLayout | Label-field pairs | [Reference](https://doc.qt.io/qt-6/qformlayout.html) |
| QGridLayout | Grid positioning | [Reference](https://doc.qt.io/qt-6/qgridlayout.html) |

## Signals and Slots

Qt's signal/slot mechanism is how widgets communicate. QtPie wraps this declaratively.

### Common Signals

```python
# QPushButton
clicked="handler"         # When button is clicked
pressed="handler"         # When mouse button goes down
released="handler"        # When mouse button comes up
toggled="handler"         # For checkable buttons (passes bool)

# QLineEdit
textChanged="handler"     # When text changes (passes str)
textEdited="handler"      # When user edits text (passes str)
returnPressed="handler"   # When Enter is pressed
editingFinished="handler" # When focus leaves or Enter pressed

# QComboBox
currentIndexChanged="handler"  # Index changed (passes int)
currentTextChanged="handler"   # Text changed (passes str)

# QSpinBox
valueChanged="handler"    # Value changed (passes int/float)

# QCheckBox
stateChanged="handler"    # Check state changed (passes int)
toggled="handler"         # Checked state changed (passes bool)
```

### Qt Documentation on Signals

- [Signals & Slots](https://doc.qt.io/qt-6/signalsandslots.html) - Core mechanism
- [PySide6 Signals Tutorial](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html)

## Style Sheets (QSS)

QSS is similar to CSS but with Qt-specific properties.

### Key References

- [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html) - Complete property list
- [Qt Style Sheets Examples](https://doc.qt.io/qt-6/stylesheet-examples.html) - Practical examples
- [Customizing Qt Widgets](https://doc.qt.io/qt-6/stylesheet-customizing.html)

### Common QSS Patterns

```css
/* By widget type */
QPushButton {
    background-color: #0078d4;
    color: white;
    border-radius: 4px;
    padding: 6px 12px;
}

/* By object name */
#submit-button {
    font-weight: bold;
}

/* By class (QtPie feature) */
.primary {
    background-color: #0078d4;
}

/* Pseudo-states */
QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #cccccc;
}
```

## Icons and Resources

### Standard Icons

Qt provides standard icons via `QStyle.StandardPixmap`:

```python
from PySide6.QtWidgets import QStyle

# Common standard icons
QStyle.StandardPixmap.SP_DialogOpenButton
QStyle.StandardPixmap.SP_DialogSaveButton
QStyle.StandardPixmap.SP_DialogCancelButton
QStyle.StandardPixmap.SP_FileIcon
QStyle.StandardPixmap.SP_DirIcon
```

- [QStyle::StandardPixmap](https://doc.qt.io/qt-6/qstyle.html#StandardPixmap-enum) - All standard icons

### Qt Resource System

- [The Qt Resource System](https://doc.qt.io/qt-6/resources.html)
- [Using .qrc Files](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/qrcfiles.html)

## Async and Event Loop

QtPie uses [qasync](https://github.com/CabbageDevelopment/qasync) for async support.

- [qasync Documentation](https://github.com/CabbageDevelopment/qasync)
- [Qt Event System](https://doc.qt.io/qt-6/eventsandfilters.html)

## Testing

### pytest-qt

QtPie's testing module wraps pytest-qt:

- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [pytest-qt GitHub](https://github.com/pytest-dev/pytest-qt)

## Books and Tutorials

### Free Resources

- [Qt for Python Tutorial](https://doc.qt.io/qtforpython-6/tutorials/index.html) - Official tutorials
- [Real Python Qt Guide](https://realpython.com/python-pyqt-layout/) - Practical tutorials

### Community

- [Qt Forum](https://forum.qt.io/) - Official community forum
- [Stack Overflow Qt Tag](https://stackoverflow.com/questions/tagged/qt) - Q&A

## Version Compatibility

QtPie supports:
- **PySide6** - Qt 6 official Python bindings (recommended)
- **PyQt6** - Alternative Qt 6 bindings

Use `qtpy` for abstraction layer if you need to support both.

## Getting Help

1. **Check Qt docs first** - Most widget behavior is standard Qt
2. **Search Qt Forum** - Common issues are usually answered
3. **Stack Overflow** - Use tags: `pyside6`, `qt6`, `python`
4. **QtPie issues** - For QtPie-specific bugs: [GitHub Issues](https://github.com/your-repo/qtpie/issues)
