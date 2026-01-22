"""DictToTupleListSync - Keeps an ObservableList of tuples in sync with a dict."""

from typing import Any, cast

from observant import ObservableDict, ObservableList


class DictToTupleListSync[K, V]:
    """Keeps an ObservableList[(K, V)] in sync with a dict or ObservableDict.

    This adapter maintains a list of (key, value) tuples that stays synchronized
    with the source dictionary. When the dict changes (insert, remove, replace, clear),
    the list is updated accordingly.

    For ObservableDict sources, changes are automatically synced via callbacks.
    For plain dict sources, the list is a snapshot (no automatic sync).

    Usage:
        obs_dict = ObservableDict({"a": 1, "b": 2})
        sync = DictToTupleListSync(obs_dict)

        # sync.list is ObservableList[tuple[str, int]]
        # When obs_dict changes, sync.list updates automatically
    """

    def __init__(self, source: ObservableDict[K, V] | dict[K, V]) -> None:
        """Initialize the sync adapter.

        Args:
            source: The source dictionary to sync with.
        """
        self._source = source
        self._is_observable = isinstance(source, ObservableDict)

        # Create initial list from dict items
        self._list: ObservableList[tuple[K, V]] = ObservableList(list(source.items()))

        # Track key -> list index for efficient updates
        self._key_to_index: dict[K, int] = {k: i for i, (k, _) in enumerate(self._list)}

        # Subscribe to dict changes if observable
        if self._is_observable:
            obs_source = cast(ObservableDict[K, V], source)
            obs_source.on_insert(self._on_insert)
            obs_source.on_remove(self._on_remove)
            obs_source.on_replace(self._on_replace)
            obs_source.on_clear(self._on_clear)

    @property
    def list(self) -> ObservableList[tuple[K, V]]:
        """Get the synced list of (key, value) tuples."""
        return self._list

    @property
    def source(self) -> ObservableDict[K, V] | dict[K, V]:
        """Get the source dictionary."""
        return self._source

    def _rebuild_index(self) -> None:
        """Rebuild the key -> index mapping after list changes."""
        self._key_to_index = {k: i for i, (k, _) in enumerate(self._list)}

    def _on_insert(self, key: K, value: V) -> None:
        """Handle new key insertion in source dict."""
        if key in self._key_to_index:
            # Key already exists (shouldn't happen, but be safe)
            return
        idx = len(self._list)
        self._list.append((key, value))
        self._key_to_index[key] = idx

    def _on_remove(self, key: K, value: V) -> None:
        """Handle key removal from source dict."""
        if key not in self._key_to_index:
            return
        idx = self._key_to_index.pop(key)
        del self._list[idx]
        # Rebuild index (indices shifted after removal)
        self._rebuild_index()

    def _on_replace(self, key: K, old_value: V, new_value: V) -> None:
        """Handle value replacement in source dict."""
        if key not in self._key_to_index:
            return
        idx = self._key_to_index[key]
        self._list[idx] = (key, new_value)

    def _on_clear(self, removed: dict[K, V]) -> None:
        """Handle dict clear."""
        self._list.clear()
        self._key_to_index.clear()

    def rename_key(self, old_key: K, new_key: K) -> bool:
        """Rename a key in the source dict and update the list.

        This is used by ReactiveTableModel.setData() when editing the #key column.

        Args:
            old_key: The current key to rename.
            new_key: The new key name.

        Returns:
            True if successful, False if old_key doesn't exist or new_key already exists.
        """
        if old_key not in self._key_to_index:
            return False
        if new_key in self._source:
            return False  # Would overwrite existing key
        if old_key == new_key:
            return True  # No-op

        # Get the value and index
        idx = self._key_to_index[old_key]
        value = self._source[old_key]

        # Update our tracking first (before dict changes trigger callbacks)
        # For ObservableDict, the callbacks will fire but be no-ops since we
        # already updated the index and list
        del self._key_to_index[old_key]
        self._key_to_index[new_key] = idx
        self._list[idx] = (new_key, value)

        # Now update the source dict
        del self._source[old_key]
        self._source[new_key] = value

        return True

    def update_value_at(self, key: K, new_value: V) -> bool:
        """Update a value in the source dict and list.

        Args:
            key: The key to update.
            new_value: The new value.

        Returns:
            True if successful, False if key doesn't exist.
        """
        if key not in self._key_to_index:
            return False

        idx = self._key_to_index[key]
        self._source[key] = new_value
        # For ObservableDict, the on_replace callback will update the list
        # For plain dict, we need to update manually
        if not self._is_observable:
            self._list[idx] = (key, new_value)

        return True

    def key_at_index(self, index: int) -> K | None:
        """Get the key at a given list index.

        Args:
            index: The list index.

        Returns:
            The key, or None if index is out of bounds.
        """
        if 0 <= index < len(self._list):
            return self._list[index][0]
        return None

    def value_at_index(self, index: int) -> V | None:
        """Get the value at a given list index.

        Args:
            index: The list index.

        Returns:
            The value, or None if index is out of bounds.
        """
        if 0 <= index < len(self._list):
            return self._list[index][1]
        return None

    def set_value_property(self, index: int, prop_name: str, prop_value: Any) -> bool:
        """Set a property on the value object at a given index.

        Used for editing columns that reference value properties.

        Args:
            index: The list index.
            prop_name: The property name to set.
            prop_value: The value to set.

        Returns:
            True if successful, False if index is out of bounds.
        """
        if not (0 <= index < len(self._list)):
            return False

        _key, value = self._list[index]
        setattr(value, prop_name, prop_value)
        return True

    def replace_source(self, new_source: ObservableDict[K, V] | dict[K, V]) -> None:
        """Replace the source dict and re-sync the list.

        Used when a binding path changes (e.g., active_environment changes).
        This updates the internal source reference and syncs the list contents.

        Args:
            new_source: The new source dictionary.
        """
        # Update source reference
        self._source = new_source
        self._is_observable = isinstance(new_source, ObservableDict)

        # Clear and rebuild list
        self._list.clear()
        self._list.extend(list(new_source.items()))
        self._rebuild_index()

        # Subscribe to new source if observable
        if self._is_observable:
            obs_source = cast(ObservableDict[K, V], new_source)
            obs_source.on_insert(self._on_insert)
            obs_source.on_remove(self._on_remove)
            obs_source.on_replace(self._on_replace)
            obs_source.on_clear(self._on_clear)
