"""Compiler that generates Qt .ts files from translation entries."""

import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement

from qtpie.translations.parser import TranslationEntry


def _find_lrelease() -> str | None:
    """
    Find the lrelease tool for compiling .ts to .qm.

    Checks in order:
    1. pyside6-lrelease (PySide6)
    2. lrelease (Qt native, works with PyQt6)

    Returns:
        Path to lrelease executable, or None if not found.
    """
    # Try PySide6's bundled lrelease
    pyside_lrelease = shutil.which("pyside6-lrelease")
    if pyside_lrelease:
        return pyside_lrelease

    # Try Qt's native lrelease (for PyQt6 or standalone Qt)
    native_lrelease = shutil.which("lrelease")
    if native_lrelease:
        return native_lrelease

    # Try running via PySide6 module (fallback)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PySide6.scripts.pyside_tool", "lrelease", "--help"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return f"{sys.executable} -m PySide6.scripts.pyside_tool lrelease"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def compile_qm(ts_path: Path | str, qm_path: Path | str | None = None) -> Path:
    """
    Compile a .ts file to .qm binary format.

    Supports both PySide6 (pyside6-lrelease) and PyQt6 (lrelease).

    Args:
        ts_path: Path to .ts file
        qm_path: Optional output path for .qm file. Defaults to same name as ts.

    Returns:
        Path to generated .qm file

    Raises:
        FileNotFoundError: If lrelease tool is not available
        RuntimeError: If compilation fails
    """
    ts_path = Path(ts_path)
    if qm_path is None:
        qm_path = ts_path.with_suffix(".qm")
    else:
        qm_path = Path(qm_path)

    lrelease = _find_lrelease()
    if lrelease is None:
        msg = "lrelease not found. Install PySide6 (includes pyside6-lrelease) or Qt tools (provides lrelease)."
        raise FileNotFoundError(msg)

    # Build command - handle the module-based invocation
    if " -m " in lrelease:
        # It's a "python -m ..." style command
        parts = lrelease.split()
        cmd = [*parts, str(ts_path), "-qm", str(qm_path)]
    else:
        cmd = [lrelease, str(ts_path), "-qm", str(qm_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        error_msg = result.stderr or result.stdout or "Unknown error"
        msg = f"lrelease failed: {error_msg}"
        raise RuntimeError(msg)

    return qm_path


def compile_all_qm(ts_files: list[Path], output_dir: Path | None = None) -> list[Path]:
    """
    Compile multiple .ts files to .qm format.

    Args:
        ts_files: List of .ts file paths
        output_dir: Optional output directory. If None, .qm files are placed
                   next to their .ts files.

    Returns:
        List of paths to generated .qm files
    """
    qm_files: list[Path] = []

    for ts_path in ts_files:
        if output_dir:
            qm_path = output_dir / ts_path.with_suffix(".qm").name
        else:
            qm_path = None

        qm_files.append(compile_qm(ts_path, qm_path))

    return qm_files


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
) -> list[Path]:
    """
    Compile translation entries to .ts files.

    Args:
        entries: List of TranslationEntry objects
        output_dir: Directory to write .ts files
        languages: Optional list of languages to compile (default: all found)

    Returns:
        List of paths to generated .ts files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    all_languages = get_all_languages(entries)
    target_languages = set(languages) if languages else all_languages

    output_files: list[Path] = []

    for lang in sorted(target_languages & all_languages):
        ts_content = compile_to_ts(entries, lang)
        output_path = output_dir / f"{lang}.ts"
        output_path.write_text(ts_content, encoding="utf-8")
        output_files.append(output_path)

    return output_files
