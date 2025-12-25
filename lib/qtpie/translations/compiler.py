"""Compiler that generates Qt .ts files from translation entries."""

from collections import defaultdict
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement

from qtpie.translations.parser import TranslationEntry


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _format_xml(element: Element, level: int = 0) -> str:
    """Format XML element with proper indentation."""
    indent = "    " * level
    result = f"{indent}<{element.tag}"

    # Add attributes
    for key, value in element.attrib.items():
        result += f' {key}="{_escape_xml(value)}"'

    if len(element) == 0 and element.text is None:
        result += "/>\n"
    elif len(element) == 0:
        text = _escape_xml(element.text) if element.text else ""
        result += f">{text}</{element.tag}>\n"
    else:
        result += ">\n"
        for child in element:
            result += _format_xml(child, level + 1)
        result += f"{indent}</{element.tag}>\n"

    return result


def compile_to_ts(entries: list[TranslationEntry], language: str) -> str:
    """
    Compile translation entries to Qt .ts XML format for a specific language.

    Args:
        entries: List of TranslationEntry objects
        language: Language code (e.g., "fr", "de", "ja")

    Returns:
        XML string in Qt .ts format
    """
    # Group entries by context
    by_context: dict[str, list[TranslationEntry]] = defaultdict(list)
    for entry in entries:
        if language in entry.translations:
            by_context[entry.context].append(entry)

    # Build XML
    ts = Element("TS")
    ts.set("version", "2.1")
    ts.set("language", language)

    for context_name in sorted(by_context.keys()):
        context_entries = by_context[context_name]

        context = SubElement(ts, "context")
        name = SubElement(context, "name")
        name.text = context_name

        for entry in context_entries:
            translation_value = entry.translations[language]

            message = SubElement(context, "message")

            # Add numerus attribute for plurals
            if isinstance(translation_value, list):
                message.set("numerus", "yes")

            # Source
            source = SubElement(message, "source")
            source.text = entry.source

            # Disambiguation comment
            if entry.disambiguation:
                comment = SubElement(message, "comment")
                comment.text = entry.disambiguation

            # Translator note
            if entry.note:
                extracomment = SubElement(message, "extracomment")
                extracomment.text = entry.note

            # Translation
            translation = SubElement(message, "translation")
            if isinstance(translation_value, list):
                # Plural forms
                for form in translation_value:
                    numerusform = SubElement(translation, "numerusform")
                    numerusform.text = form
            else:
                translation.text = translation_value

    # Generate XML with declaration
    xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n'
    return xml_declaration + _format_xml(ts)


def get_all_languages(entries: list[TranslationEntry]) -> set[str]:
    """Get all language codes from translation entries."""
    languages: set[str] = set()
    for entry in entries:
        languages.update(entry.translations.keys())
    return languages


def compile_translations(
    entries: list[TranslationEntry],
    output_dir: Path,
    *,
    languages: list[str] | None = None,
    prefix: str = "",
) -> list[Path]:
    """
    Compile translation entries to .ts files.

    Args:
        entries: List of TranslationEntry objects
        output_dir: Directory to write .ts files
        languages: Optional list of languages to compile (default: all found)
        prefix: Optional prefix for output filenames (e.g., "myapp_")

    Returns:
        List of paths to generated .ts files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    all_languages = get_all_languages(entries)
    target_languages = set(languages) if languages else all_languages

    output_files: list[Path] = []

    for lang in sorted(target_languages & all_languages):
        ts_content = compile_to_ts(entries, lang)
        output_path = output_dir / f"{prefix}{lang}.ts"
        output_path.write_text(ts_content, encoding="utf-8")
        output_files.append(output_path)

    return output_files
