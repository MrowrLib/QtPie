"""QtPie translation system.

Provides internationalization (i18n) support with:
- YAML-based translation files
- Hot-reload during development
- Compilation to Qt's .ts/.qm formats for production
"""

from qtpie.translations.compiler import (
    compile_all_qm,
    compile_qm,
    compile_to_ts,
    compile_translations,
    get_all_languages,
)
from qtpie.translations.loader import can_watch_path, is_qrc_path, read_file_content
from qtpie.translations.parser import (
    TranslationEntry,
    deep_merge,
    parse_source_key,
    parse_yaml,
    parse_yaml_files,
)
from qtpie.translations.store import (
    clear_bindings,
    clear_translations,
    get_binding_count,
    get_format_binding_count,
    get_language,
    load_translations_from_entries,
    load_translations_from_yaml,
    lookup,
    lookup_plural,
    register_binding,
    register_format_binding,
    reload_translations,
    retranslate_all,
    set_language,
)
from qtpie.translations.translatable import (
    Translatable,
    enable_memory_store,
    get_translation_context,
    is_memory_store_enabled,
    resolve_translatable,
    set_translation_context,
    t,
)
from qtpie.translations.watcher import TranslationWatcher, watch_translations

__all__ = [
    # Core
    "Translatable",
    "t",
    # Context
    "enable_memory_store",
    "get_translation_context",
    "is_memory_store_enabled",
    "resolve_translatable",
    "set_translation_context",
    # Store
    "clear_bindings",
    "clear_translations",
    "get_binding_count",
    "get_format_binding_count",
    "get_language",
    "load_translations_from_entries",
    "load_translations_from_yaml",
    "lookup",
    "lookup_plural",
    "register_binding",
    "register_format_binding",
    "reload_translations",
    "retranslate_all",
    "set_language",
    # Parser
    "TranslationEntry",
    "deep_merge",
    "parse_source_key",
    "parse_yaml",
    "parse_yaml_files",
    # Loader
    "can_watch_path",
    "is_qrc_path",
    "read_file_content",
    # Compiler
    "compile_all_qm",
    "compile_qm",
    "compile_to_ts",
    "compile_translations",
    "get_all_languages",
    # Watcher
    "TranslationWatcher",
    "watch_translations",
]
