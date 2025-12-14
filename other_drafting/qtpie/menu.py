from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Callable, TypeVar, dataclass_transform

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

T = TypeVar("T", bound=QMenu)


@dataclass_transform()
def menu(text: str | None = None) -> Callable[[type[T]], type[T]]:
    def decorator(cls: type[T]) -> type[T]:
        if not is_dataclass(cls):
            cls = dataclass(cls)

        original_init = cls.__init__

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            original_init(self, *args, **kwargs)  # ✅ dataclass sets fields
            super(type(self), self).__init__()  # ✅ Qt base initialized (NO kwargs!)

            if original_init is not QMenu.__init__:
                original_init(self, *args, **kwargs)

            for field in fields(self.__class__):
                field_instance = getattr(self, field.name, None)
                if isinstance(field_instance, QMenu):
                    self.addMenu(field_instance)
                elif isinstance(field_instance, QAction):
                    self.addAction(field_instance)

            if text:
                self.setTitle(text)

        cls.__init__ = new_init
        return cls

    return decorator
