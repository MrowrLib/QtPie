"""YAML parser for translation files."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from qtpie.translations.loader import read_file_content


@dataclass
class TranslationEntry:
    """A single translation entry."""

    context: str
    source: str
    disambiguation: str | None
    note: str | None
    translations: dict[str, str | list[str]]

    @property
    def is_plural(self) -> bool:
        """Check if any translation is a plural (list of forms)."""
        return any(isinstance(v, list) for v in self.translations.values())


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Values from overlay override values in base.
    Nested dicts are merged recursively.
    """
    result = base.copy()

    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(
                cast(dict[str, Any], result[key]),
                cast(dict[str, Any], value),
            )
        else:
            result[key] = value

    return result


def parse_source_key(key: str) -> tuple[str, str | None]:
    """
    Parse a source key that may contain disambiguation.

    "Open" -> ("Open", None)
    "Open|menu" -> ("Open", "menu")
    "%n file(s)|selected" -> ("%n file(s)", "selected")
    """
    if "|" in key:
        parts = key.split("|", 1)
        return parts[0], parts[1]
    return key, None


def parse_yaml(content: str) -> list[TranslationEntry]:
    """
    Parse YAML translation content into TranslationEntry objects.

    Supports:
    - :global: context for shared strings
    - Regular context names (class names)
    - Disambiguation with pipe: "Source|comment"
    - Translator notes with :note:
    - Plurals as arrays
    """
    data: dict[str, Any] = yaml.safe_load(content) or {}
    entries: list[TranslationEntry] = []

    for context_key, messages in data.items():
        # :global: becomes @default context (YAML parses ":global:" as ":global")
        context_key_str = str(context_key)
        context = "@default" if context_key_str == ":global" else context_key_str

        if not isinstance(messages, dict):
            continue

        messages_typed = cast(dict[str, Any], messages)
        for source_key, value in messages_typed.items():
            if not isinstance(value, dict):
                continue

            # Convert source_key to string (YAML parses Yes/No/True/False as bool)
            source, disambiguation = parse_source_key(str(source_key))

            # Extract note and translations
            note: str | None = None
            translations: dict[str, str | list[str]] = {}

            value_typed = cast(dict[str, Any], value)
            for lang_or_meta, translation in value_typed.items():
                lang_key = str(lang_or_meta)
                # YAML parses ":note:" as ":note"
                if lang_key == ":note":
                    note = str(translation)
                elif isinstance(translation, str):
                    translations[lang_key] = translation
                elif isinstance(translation, list):
                    # Plural forms - cast list items to Any for str() conversion
                    forms = cast(list[Any], translation)
                    translations[lang_key] = [str(form) for form in forms]

            if translations:
                entries.append(
                    TranslationEntry(
                        context=context,
                        source=source,
                        disambiguation=disambiguation,
                        note=note,
                        translations=translations,
                    )
                )

    return entries


def parse_yaml_files(paths: Sequence[Path | str] | Path | str) -> list[TranslationEntry]:
    """
    Parse multiple YAML files and deep merge them.

    Files are merged in order, with later files overriding earlier ones.
    Supports both filesystem paths and QRC paths (e.g., ":/translations/app.yml").

    Args:
        paths: Single path or list of paths. Can be Path objects (filesystem)
               or strings (filesystem or QRC paths starting with ":/" ).
    """
    # Normalize to list of strings
    if isinstance(paths, (str, Path)):
        path_list: list[str] = [str(paths)]
    else:
        path_list = [str(p) for p in paths]

    merged: dict[str, Any] = {}

    for path in path_list:
        content = read_file_content(path)
        if content is None:
            continue

        loaded = yaml.safe_load(content)
        if isinstance(loaded, dict):
            data = cast(dict[str, Any], loaded)
        else:
            data = {}
        merged = deep_merge(merged, data)

    # Convert merged dict back to YAML string and parse
    merged_yaml = yaml.dump(merged, allow_unicode=True)
    return parse_yaml(merged_yaml)
