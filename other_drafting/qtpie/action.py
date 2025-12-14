from dataclasses import dataclass, is_dataclass
from typing import Any, Callable, TypeVar, dataclass_transform

from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QStyle

from qtpie.signal_typing import as_bool_handler

T = TypeVar("T", bound=QAction)


@dataclass_transform()
def action(
    text: str | None = None,
    *,
    shortcut: str | None = None,
    tooltip: str | None = None,
    icon: QPixmap | QIcon | QStyle.StandardPixmap | str | None = None,
) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        if not is_dataclass(cls):
            cls = dataclass(cls)

        original_init = cls.__init__

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)  # ✅ dataclass sets fields
            super(type(self), self).__init__()  # ✅ Qt base initialized (NO kwargs!)

            if original_init is not QAction.__init__:
                original_init(self, *args, **kwargs)

            if text:
                self.setText(text)

            if shortcut:
                self.setShortcut(shortcut)

            if tooltip:
                self.setStatusTip(tooltip)

            if icon:
                if isinstance(icon, str):
                    self.setIcon(QIcon(icon))
                elif isinstance(icon, (QPixmap, QIcon)):
                    self.setIcon(icon)
                else:
                    app = QApplication.instance()
                    if isinstance(app, QApplication):
                        self.setIcon(app.style().standardIcon(icon))
                    else:
                        print("QApplication instance not found, cannot set icon")

            self.triggered.connect(as_bool_handler(lambda checked: self.action(checked)))

        cls.__init__ = new_init
        return cls

    return decorator
