"""In-memory translation store for development hot-reload."""

from pathlib import Path
from weakref import ref

from qtpy.QtCore import QObject

from qtpie.translations.parser import TranslationEntry, parse_yaml_files

# Type alias for translation key: (context, source, disambiguation)
TranslationKey = tuple[str, str, str | None]

# In-memory translation storage
# Key: (context, source, disambiguation)
# Value: {language_code: translated_text}
_translations: dict[TranslationKey, dict[str, str | list[str]]] = {}

# Current language for lookups
_current_language: str = "en"

# Bindings registry: (widget_weakref, property_name, source_text, disambiguation)
# We store source_text instead of Translatable to avoid circular import
_translation_bindings: list[tuple[ref[QObject], str, str, str | None]] = []

# Loaded YAML paths (for reloading)
_loaded_paths: list[Path] = []


def set_language(language: str) -> None:
    """Set the current language for translation lookups."""
    global _current_language
    _current_language = language


def get_language() -> str:
    """Get the current language."""
    return _current_language


def load_translations_from_yaml(paths: list[Path] | Path) -> None:
    """
    Load translations from YAML file(s) into memory.

    Args:
        paths: Single path or list of paths to YAML files.
               Multiple files are deep-merged.
    """
    global _loaded_paths

    if isinstance(paths, Path):
        paths = [paths]

    _loaded_paths = list(paths)
    _translations.clear()

    entries = parse_yaml_files(paths)
    for entry in entries:
        key: TranslationKey = (entry.context, entry.source, entry.disambiguation)
        _translations[key] = entry.translations


def load_translations_from_entries(entries: list[TranslationEntry]) -> None:
    """Load translations from pre-parsed entries."""
    _translations.clear()
    for entry in entries:
        key: TranslationKey = (entry.context, entry.source, entry.disambiguation)
        _translations[key] = entry.translations


def reload_translations() -> None:
    """Reload translations from previously loaded YAML paths."""
    if _loaded_paths:
        load_translations_from_yaml(_loaded_paths)


def lookup(
    context: str,
    source: str,
    disambiguation: str | None = None,
) -> str:
    """
    Look up translation for the current language.

    Args:
        context: Translation context (usually class name)
        source: Source text to translate
        disambiguation: Optional disambiguation string

    Returns:
        Translated text, or source text if no translation found.
    """
    key: TranslationKey = (context, source, disambiguation)

    if key in _translations:
        lang_translations = _translations[key]
        if _current_language in lang_translations:
            result = lang_translations[_current_language]
            # Handle plural forms - return first form for simple lookup
            if isinstance(result, list):
                return result[0] if result else source
            return result

    # Fallback: try without disambiguation
    if disambiguation is not None:
        key_no_disambig: TranslationKey = (context, source, None)
        if key_no_disambig in _translations:
            lang_translations = _translations[key_no_disambig]
            if _current_language in lang_translations:
                result = lang_translations[_current_language]
                if isinstance(result, list):
                    return result[0] if result else source
                return result

    # No translation found - return source
    return source


def register_binding(
    widget: QObject,
    property_name: str,
    source: str,
    disambiguation: str | None = None,
) -> None:
    """
    Register a translation binding for later retranslation.

    Args:
        widget: The widget to update
        property_name: Property to set (e.g., "text", "placeholderText")
        source: Source text
        disambiguation: Optional disambiguation
    """
    _translation_bindings.append((ref(widget), property_name, source, disambiguation))


def retranslate_all(context: str | None = None) -> None:
    """
    Re-apply all translations.

    Call this after changing language or reloading YAML.

    Args:
        context: Optional context to filter by (retranslate only widgets
                 from this context). If None, retranslates all.
    """
    from qtpie.translations.translatable import get_translation_context

    live_bindings: list[tuple[ref[QObject], str, str, str | None]] = []

    for widget_ref, prop, source, disambiguation in _translation_bindings:
        widget = widget_ref()
        if widget is not None:
            # Get the context for this lookup
            # For now, use the global context (set by @widget decorator)
            ctx = context or get_translation_context()
            translated = lookup(ctx, source, disambiguation)
            widget.setProperty(prop, translated)
            live_bindings.append((widget_ref, prop, source, disambiguation))

    # Clean up dead references
    _translation_bindings[:] = live_bindings


def clear_bindings() -> None:
    """Clear all translation bindings. Useful for tests."""
    _translation_bindings.clear()


def clear_translations() -> None:
    """Clear all loaded translations. Useful for tests."""
    _translations.clear()
    _loaded_paths.clear()


def get_binding_count() -> int:
    """Get number of registered bindings. Useful for tests."""
    return len(_translation_bindings)
