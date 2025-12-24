from typing import Generic, TypeVar

from attr import dataclass
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QBoxLayout, QLayout, QWidget

from mrowr.observable_proxy import ObservableProxy
from qtpie.styles import QtStyleClass

T = TypeVar("T")


class Widget:
    def setup(self) -> None:
        pass

    def setup_bindings(self) -> None:
        pass

    def setup_layout(self, layout: QLayout) -> None:
        pass

    def setup_box_layout(self, layout: QBoxLayout) -> None:
        pass

    def setup_styles(self) -> None:
        pass

    def setup_events(self) -> None:
        pass

    def setup_values(self) -> None:
        pass

    def setup_signals(self) -> None:
        pass

    def add_class(self, class_name: str) -> None:
        if isinstance(self, QObject):
            QtStyleClass.add_class(self, class_name)

    def remove_class(self, class_name: str) -> None:
        if isinstance(self, QObject):
            QtStyleClass.remove_class(self, class_name)

    def replace_class(self, old_class_name: str, new_class_name: str) -> None:
        if isinstance(self, QObject):
            QtStyleClass.replace_class(self, old_class_name, new_class_name)

    def toggle_class(self, class_name: str) -> None:
        if isinstance(self, QObject):
            QtStyleClass.toggle_class(self, class_name)

    def add_widget(self, widget: QWidget) -> None:
        if isinstance(self, QWidget):
            layout = self.layout()
            if layout is None:
                raise ValueError("Cannot add widget to QWidget without a layout.")
            if isinstance(layout, QBoxLayout):
                layout.addWidget(widget)
        else:
            raise TypeError("Cannot add widget to non-QWidget instance.")

    def remove_widget(self, widget: QWidget) -> None:
        if isinstance(self, QWidget):
            layout = self.layout()
            if layout is None:
                raise ValueError("Cannot remove widget from QWidget without a layout.")
            if isinstance(layout, QBoxLayout):
                layout.removeWidget(widget)
        else:
            raise TypeError("Cannot remove widget from non-QWidget instance.")


class WidgetModel(Generic[T]):
    _object: T
    _proxy: ObservableProxy[T]

    def __init__(self, obj: T):
        self._object = obj
        self._proxy = ObservableProxy(self._object, sync=False)
        # self._proxy = ObservableProxy(self._object, sync=True)

    @property
    def value(self):
        return self._object

    @property
    def proxy(self):
        return self._proxy


@dataclass
class ModelWidget(Widget, Generic[T]):
    _bound_widget_model: WidgetModel[T] | None = None

    @property
    def model(self) -> WidgetModel[T] | None:
        """Returns the model bound to this widget."""
        return self._bound_widget_model

    def set_model(self, model: T) -> None:
        """Sets the model for this widget."""
        self._bound_widget_model = WidgetModel(model)
        self.setup_model(self._bound_widget_model)

    def set_widget_model(self, model: WidgetModel[T]) -> None:
        """Sets the model for this widget."""
        self._bound_widget_model = model
        self.setup_model(self._bound_widget_model)

    def setup_model(self, model: WidgetModel[T]) -> None:
        pass

    def teardown_model(self, model: WidgetModel[T]) -> None:
        pass

    def reset_model(self) -> None:
        """Resets the model for this widget."""
        self._bound_widget_model = None


class Action:
    def action(self, checked: bool) -> None:
        """Defines the default action behavior for QAction instances."""
        pass
