"""File watcher for translation hot-reload."""

from pathlib import Path

from qtpy.QtCore import QFileSystemWatcher, QObject, QTimer, Signal

from qtpie.translations.store import (
    load_translations_from_yaml,
    retranslate_all,
)


class TranslationWatcher(QObject):
    """
    Watch YAML translation files and hot-reload on changes.

    Similar to QssWatcher but for translations. When YAML files change:
    1. Reload translations into memory
    2. Re-apply to all registered widgets via setProperty()
    """

    translationsReloaded = Signal()

    def __init__(
        self,
        yaml_paths: list[Path] | Path,
        language: str = "en",
        parent: QObject | None = None,
    ) -> None:
        """
        Create a translation watcher.

        Args:
            yaml_paths: Path or list of paths to YAML translation files.
            language: Language code to use for lookups.
            parent: Optional parent QObject.
        """
        super().__init__(parent)

        if isinstance(yaml_paths, Path):
            yaml_paths = [yaml_paths]

        self._yaml_paths = [p.resolve() for p in yaml_paths]
        self._language = language
        self._mtimes: dict[str, float] = {}

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_changed)
        self._watcher.fileChanged.connect(self._on_changed)

        # Debounce timer - 150ms handles editor multi-step saves
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._reload_if_changed)

        # Watch each YAML file and its parent directory
        for yaml_path in self._yaml_paths:
            if yaml_path.parent.exists():
                self._watcher.addPath(str(yaml_path.parent))
            self._ensure_file_watched(yaml_path)

        # Initial load
        self._reload_if_changed(initial=True)

    def _ensure_file_watched(self, path: Path) -> None:
        """Ensure file is in watch list (re-arms after delete/rename)."""
        if path.exists():
            path_str = str(path)
            if path_str not in self._watcher.files():
                self._watcher.addPath(path_str)

    def _on_changed(self, path: str) -> None:
        """File or directory changed."""
        changed = Path(path)

        # Re-arm file watch if it was replaced
        if changed.is_file():
            self._ensure_file_watched(changed)

        # If directory changed, re-watch YAML files in it
        if changed.is_dir():
            for yaml_path in self._yaml_paths:
                if yaml_path.parent == changed:
                    self._ensure_file_watched(yaml_path)

        self._debounce_timer.start()

    def _get_mtimes(self) -> dict[str, float]:
        """Get modification times for all watched files."""
        mtimes: dict[str, float] = {}
        for yaml_path in self._yaml_paths:
            if yaml_path.exists():
                try:
                    mtimes[str(yaml_path)] = yaml_path.stat().st_mtime
                except OSError:
                    pass
        return mtimes

    def _reload_if_changed(self, initial: bool = False) -> None:
        """Reload translations if any file actually changed."""
        # Check if any file changed
        current_mtimes = self._get_mtimes()
        if not initial and current_mtimes == self._mtimes:
            return

        self._mtimes = current_mtimes

        # Check all files exist
        existing_paths = [p for p in self._yaml_paths if p.exists()]
        if not existing_paths:
            return

        try:
            # Enable memory store mode
            from qtpie.translations.translatable import enable_memory_store

            enable_memory_store(True)

            # Set language
            from qtpie.translations.store import set_language

            set_language(self._language)

            # Reload translations
            load_translations_from_yaml(existing_paths)

            # Retranslate all widgets
            retranslate_all()

            self.translationsReloaded.emit()

        except Exception:
            # Don't crash on YAML errors - keep old translations
            pass

    def set_language(self, language: str) -> None:
        """
        Change the current language and retranslate all widgets.

        Args:
            language: New language code.
        """
        from qtpie.translations.store import set_language

        self._language = language
        set_language(language)
        retranslate_all()
        self.translationsReloaded.emit()

    def stop(self) -> None:
        """Stop watching."""
        self._debounce_timer.stop()
        self._watcher.directoryChanged.disconnect(self._on_changed)
        self._watcher.fileChanged.disconnect(self._on_changed)


def watch_translations(
    yaml_paths: list[Path] | Path,
    language: str = "en",
) -> TranslationWatcher:
    """
    Watch YAML translation files and hot-reload on changes.

    Args:
        yaml_paths: Path or list of paths to YAML files.
        language: Language code for lookups.

    Returns:
        TranslationWatcher instance. Keep a reference to prevent garbage collection.
    """
    return TranslationWatcher(yaml_paths, language)
