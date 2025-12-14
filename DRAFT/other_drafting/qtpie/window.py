from dataclasses import dataclass, is_dataclass
from typing import Any, Callable, TypeVar, dataclass_transform

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QMenu

from qtpie.styles import QtStyleClass

T = TypeVar("T", bound=QMainWindow)


@dataclass_transform()
def window(
    _cls: type[T] | None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    icon: str | None = None,
    size: tuple[int, int] | None = None,
) -> Callable[[type[T]], type[T]] | type[T]:
    def decorator(cls: type[T]) -> type[T]:
        if not is_dataclass(cls):
            cls = dataclass(cls)

        original_init = cls.__init__

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)  # ✅ dataclass sets fields
            super(type(self), self).__init__()  # ✅ Qt base initialized (NO kwargs!)

            self.setup()
            self.setup_bindings()
            if self.layout() is not None:
                self.setup_layout(self.layout())
            self.setup_styles()
            self.setup_events()
            self.setup_signals()

            if name:
                self.setObjectName(name)
            else:
                self.setObjectName(cls.__name__)
            if classes:
                QtStyleClass.set_classes(self, classes)
            if title:
                self.setWindowTitle(title)
            if icon:
                self.setWindowIcon(QPixmap(icon))
            if size:
                self.resize(*size)

            if hasattr(self, "central_widget") and self.central_widget is not None:
                self.setCentralWidget(self.central_widget)

            for field_name in getattr(self, "__dataclass_fields__", {}):
                field_value = getattr(self, field_name, None)
                if isinstance(field_value, QMenu):
                    self.menuBar().addMenu(field_value)

        cls.__init__ = new_init
        return cls

    if _cls is not None:
        return decorator(_cls)
    return decorator
