"""In-memory translation store for development hot-reload."""

from collections.abc import Callable, Sequence
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

# Loaded YAML paths (for reloading) - can be Path or str (for QRC paths)
_loaded_paths: list[Path | str] = []

# Format binding callbacks: (translatable_source, disambiguation, callback to recompute)
# The callback takes the resolved format string and recomputes the formatted value
FormatBindingCallback = Callable[[str], None]
_format_bindings: list[tuple[ref[QObject], str, str | None, FormatBindingCallback]] = []


def set_language(language: str) -> None:
    """Set the current language for translation lookups."""
    global _current_language
    _current_language = language


def get_language() -> str:
    """Get the current language."""
    return _current_language


def load_translations_from_yaml(paths: Sequence[Path | str] | Path | str) -> None:
    """
    Load translations from YAML file(s) into memory.

    Args:
        paths: Single path or list of paths to YAML files.
               Can be Path objects or strings (including QRC paths like ":/translations/app.yml").
               Multiple files are deep-merged.
    """
    global _loaded_paths

    # Normalize to list
    if isinstance(paths, (str, Path)):
        path_list: list[Path | str] = [paths]
    else:
        path_list = list(paths)

    _loaded_paths = path_list
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

    # Fallback: try @default context (for :global: translations)
    if context != "@default":
        return lookup("@default", source, disambiguation)

    # No translation found - return source
    return source


def lookup_plural(
    context: str,
    source: str,
    n: int,
    disambiguation: str | None = None,
) -> str:
    """
    Look up plural translation for the current language.

    Args:
        context: Translation context (usually class name)
        source: Source text to translate
        n: Count for plural form selection
        disambiguation: Optional disambiguation string

    Returns:
        Translated plural text with %n replaced, or source text if no translation.
    """
    key: TranslationKey = (context, source, disambiguation)

    if key in _translations:
        lang_translations = _translations[key]
        if _current_language in lang_translations:
            result = lang_translations[_current_language]
            if isinstance(result, list) and result:
                # Select plural form based on count
                # Simple rule: index 0 for n==1, index 1 for n!=1
                # (works for English, French, etc. - not all languages)
                form_index = 0 if n == 1 else min(1, len(result) - 1)
                return result[form_index].replace("%n", str(n))
            elif isinstance(result, str):
                return result.replace("%n", str(n))

    # Fallback: try without disambiguation
    if disambiguation is not None:
        return lookup_plural(context, source, n, None)

    # Fallback: try @default context
    if context != "@default":
        return lookup_plural("@default", source, n, disambiguation)

    # No translation found - return source with %n replaced
    return source.replace("%n", str(n))


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


def register_format_binding(
    widget: QObject,
    source: str,
    disambiguation: str | None,
    callback: FormatBindingCallback,
) -> None:
    """
    Register a format binding for later retranslation.

    This is used for bind=tr["Count: {count}"] where the format string
    needs to be re-resolved when translations change.

    Args:
        widget: The widget (used for weak reference to track lifetime)
        source: Source text of the Translatable
        disambiguation: Optional disambiguation
        callback: Function to call with the resolved format string
    """
    _format_bindings.append((ref(widget), source, disambiguation, callback))


def retranslate_all(context: str | None = None) -> None:
    """
    Re-apply all translations.

    Call this after changing language or reloading YAML.

    Args:
        context: Optional context to filter by (retranslate only widgets
                 from this context). If None, retranslates all.
    """
    from qtpie.translations.translatable import get_translation_context

    # Get context for lookups
    ctx = context or get_translation_context()

    # Process simple property bindings
    live_bindings: list[tuple[ref[QObject], str, str, str | None]] = []

    for widget_ref, prop, source, disambiguation in _translation_bindings:
        widget = widget_ref()
        if widget is not None:
            translated = lookup(ctx, source, disambiguation)
            widget.setProperty(prop, translated)
            live_bindings.append((widget_ref, prop, source, disambiguation))

    # Clean up dead references
    _translation_bindings[:] = live_bindings

    # Process format bindings (bind=tr["Count: {count}"])
    live_format_bindings: list[tuple[ref[QObject], str, str | None, FormatBindingCallback]] = []

    for widget_ref, source, disambiguation, callback in _format_bindings:
        widget = widget_ref()
        if widget is not None:
            # Re-resolve the format string with new translation
            translated_format = lookup(ctx, source, disambiguation)
            # Call the callback with the new format string
            callback(translated_format)
            live_format_bindings.append((widget_ref, source, disambiguation, callback))

    # Clean up dead references
    _format_bindings[:] = live_format_bindings


def clear_bindings() -> None:
    """Clear all translation bindings. Useful for tests."""
    _translation_bindings.clear()
    _format_bindings.clear()


def clear_translations() -> None:
    """Clear all loaded translations. Useful for tests."""
    _translations.clear()
    _loaded_paths.clear()


def get_binding_count() -> int:
    """Get number of registered bindings (both simple and format). Useful for tests."""
    return len(_translation_bindings) + len(_format_bindings)


def get_format_binding_count() -> int:
    """Get number of registered format bindings. Useful for tests."""
    return len(_format_bindings)
