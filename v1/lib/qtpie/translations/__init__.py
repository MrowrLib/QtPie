"""QtPie translations - YAML to Qt .ts compiler with hot-reload support."""

from qtpie.translations.compiler import (
    compile_all_qm,
    compile_qm,
    compile_translations,
)
from qtpie.translations.parser import TranslationEntry, parse_yaml, parse_yaml_files
from qtpie.translations.store import (
    clear_bindings,
    clear_translations,
    get_language,
    load_translations_from_yaml,
    lookup,
    register_binding,
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
    tr,
)
from qtpie.translations.watcher import TranslationWatcher, watch_translations

__all__ = [
    "TranslationEntry",
    "TranslationWatcher",
    "Translatable",
    "clear_bindings",
    "clear_translations",
    "compile_all_qm",
    "compile_qm",
    "compile_translations",
    "enable_memory_store",
    "get_language",
    "get_translation_context",
    "is_memory_store_enabled",
    "load_translations_from_yaml",
    "lookup",
    "parse_yaml",
    "parse_yaml_files",
    "register_binding",
    "resolve_translatable",
    "retranslate_all",
    "set_language",
    "set_translation_context",
    "tr",
    "watch_translations",
]
