"""ReactiveListModel - QAbstractListModel backed by ObservableList."""

from collections.abc import Callable
from typing import Any, override

from observant import ObservableList
from qtpy.QtCore import QAbstractListModel, QModelIndex, QObject, QPersistentModelIndex, Qt


class ReactiveListModel[T](QAbstractListModel):
    """QAbstractListModel backed by ObservableList[T].

    Emits proper Qt model signals when the ObservableList changes:
    - on_insert -> beginInsertRows/endInsertRows
    - on_remove -> beginRemoveRows/endRemoveRows
    - on_replace -> dataChanged
    - on_clear -> beginResetModel/endResetModel

    Usage:
        obs_list = ObservableList(["A", "B", "C"])
        model = ReactiveListModel(obs_list)
        combo.setModel(model)

        # Changes to obs_list automatically update the view
        obs_list.append("D")  # Emits rowsInserted
        obs_list.remove("A")  # Emits rowsRemoved

        # With custom formatting for complex objects:
        dogs = ObservableList([Dog("Fido", 3), Dog("Rex", 5)])
        model = ReactiveListModel(dogs, format_fn=lambda d: f"{d.name} ({d.age})")
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        format_fn: Callable[[T], str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._format_fn = format_fn

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        """Return number of rows in the model."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._obs_list)

    @override
    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self._obs_list):
            return None

        item = self._obs_list[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if self._format_fn is not None:
                return self._format_fn(item)
            return str(item)
        elif role == Qt.ItemDataRole.UserRole:
            # Return the actual item for programmatic access
            return item

        return None

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self.beginInsertRows(QModelIndex(), index, index)
        self.endInsertRows()

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        self.beginRemoveRows(QModelIndex(), index, index)
        self.endRemoveRows()

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index)

    def _on_clear(self, items: list[T]) -> None:
        """Handle list clear."""
        self.beginResetModel()
        self.endResetModel()

    # Convenience methods

    def item_at(self, index: int) -> T | None:
        """Get the item at a given index."""
        if 0 <= index < len(self._obs_list):
            return self._obs_list[index]
        return None

    def index_of(self, item: T) -> int:
        """Find the index of an item, returns -1 if not found."""
        try:
            return list(self._obs_list).index(item)
        except ValueError:
            return -1
