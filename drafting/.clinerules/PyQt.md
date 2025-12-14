# PyQt

We're using `pyqt` so this means your imports should be like this:

```python
from qtpy.QtWidgets import QWidget
```

- Do NOT import from `PySide6` directly.

# QtBot fixture

If you need to use the `QtBot` fixture in your tests, make sure to import it from `qtpy`:

```python
from pytestqt.qtbot import QtBot
```

And in every test which creates a `QWidget` or derived class, you should use the `QtBot` fixture like this:

```python
def test_my_widget(qtbot: QtBot):
    widget = MyWidget()
    # qtbot.addWidget(widget) <--- addWidget is NOT required, only use it when showing the widget
    
def test_showing_widget(qtbot: QtBot):
    widget = MyWidget()
    qtbot.addWidget(widget)  # This is needed if you want to show the widget
    widget.show()
```