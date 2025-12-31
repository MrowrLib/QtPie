from dataclasses import dataclass
from typing import Any, override


class QSlider:
    pass


class QPushButton:
    pass


class QLineEdit:
    pass


class QLabel:
    pass


class Widget[T = None]:
    def on_valid_changed(self) -> None:
        pass

    def on_dirty_changed(self) -> None:
        pass

    @property
    def view_model(self) -> T:
        return None  # type: ignore


class Variable[T, W = None]:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


def new(*args: Any, **kwargs: Any) -> Any:
    pass


def widget(cls: Any) -> Any:
    return cls


@widget
class MyWidget(Widget):
    # Just a simple string variable, changes to it are reactive in the UI
    _name: Variable[str] = new()

    # An integer variable automatically represented by a slider in the UI
    _age: Variable[int, QSlider] = new(min=0, max=120, step=1, default=25)

    # A single line edit for editing the name variable
    _name_edit: QLineEdit = new(bind=_name)

    # A button that prints a greeting when clicked
    _greet_button: QPushButton = new(clicked="on_click")

    # Some text label which shows the name and age (updates automatically)
    _label: QLabel = new(bind="{_name}, {_age} years old")

    @override
    def on_dirty_changed(self) -> None: ...

    @override
    def on_valid_changed(self) -> None: ...

    def on_click(self) -> None:
        print(f"Hello, {self._name}!")


# And is you decide to optionally use a more MVVM approach...


@dataclass
class MyViewModel:
    name: str
    age: int


@widget
class MyWidgetMVVM(Widget[MyViewModel]):
    _name_edit: QLineEdit = new(bind="name")
    _age_slider: QSlider = new(bind="age", min=0, max=120, step=1)
    _greet_button: QPushButton = new(clicked="on_click")
    _label: QLabel = new(bind="{name}, {age} years old")

    def on_click(self) -> None:
        print(f"Hello, {self.view_model.name}!")
