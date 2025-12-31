"""Tests for the translations .ts compiler."""

from pathlib import Path

from assertpy import assert_that

from qtpie.translations.compiler import (
    compile_to_ts,
    compile_translations,
    get_all_languages,
)
from qtpie.translations.parser import TranslationEntry


class TestGetAllLanguages:
    """Tests for get_all_languages function."""

    def test_single_entry_single_language(self) -> None:
        """Single entry with one language."""
        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"fr": "Bonjour"},
            )
        ]
        languages = get_all_languages(entries)
        assert_that(languages).is_equal_to({"fr"})

    def test_multiple_languages(self) -> None:
        """Multiple entries with different languages."""
        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"fr": "Bonjour", "de": "Hallo"},
            ),
            TranslationEntry(
                context="Test",
                source="World",
                disambiguation=None,
                note=None,
                translations={"ja": "世界"},
            ),
        ]
        languages = get_all_languages(entries)
        assert_that(languages).is_equal_to({"fr", "de", "ja"})


class TestCompileToTs:
    """Tests for compile_to_ts function."""

    def test_basic_translation(self) -> None:
        """Compile basic translation entry."""
        entries = [
            TranslationEntry(
                context="LoginDialog",
                source="Username",
                disambiguation=None,
                note=None,
                translations={"fr": "Nom d'utilisateur"},
            )
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains('<?xml version="1.0" encoding="utf-8"?>')
        assert_that(xml).contains("<!DOCTYPE TS>")
        assert_that(xml).contains('<TS version="2.1" language="fr">')
        assert_that(xml).contains("<name>LoginDialog</name>")
        assert_that(xml).contains("<source>Username</source>")
        assert_that(xml).contains("<translation>Nom d'utilisateur</translation>")

    def test_disambiguation(self) -> None:
        """Compile entry with disambiguation comment."""
        entries = [
            TranslationEntry(
                context="MainWindow",
                source="Open",
                disambiguation="menu",
                note=None,
                translations={"fr": "Ouvrir"},
            )
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains("<source>Open</source>")
        assert_that(xml).contains("<comment>menu</comment>")
        assert_that(xml).contains("<translation>Ouvrir</translation>")

    def test_translator_note(self) -> None:
        """Compile entry with translator note."""
        entries = [
            TranslationEntry(
                context="MainWindow",
                source="Save changes?",
                disambiguation=None,
                note="Shown when closing with unsaved work",
                translations={"fr": "Enregistrer les modifications ?"},
            )
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains("<source>Save changes?</source>")
        assert_that(xml).contains("<extracomment>Shown when closing with unsaved work</extracomment>")

    def test_plural_forms(self) -> None:
        """Compile entry with plural forms."""
        entries = [
            TranslationEntry(
                context="MainWindow",
                source="%n file(s)",
                disambiguation=None,
                note=None,
                translations={"fr": ["%n fichier", "%n fichiers"]},
            )
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains('numerus="yes"')
        assert_that(xml).contains("<numerusform>%n fichier</numerusform>")
        assert_that(xml).contains("<numerusform>%n fichiers</numerusform>")

    def test_russian_plural_forms(self) -> None:
        """Compile entry with Russian 3-form plurals."""
        entries = [
            TranslationEntry(
                context="MainWindow",
                source="%n file(s)",
                disambiguation=None,
                note=None,
                translations={"ru": ["%n файл", "%n файла", "%n файлов"]},
            )
        ]

        xml = compile_to_ts(entries, "ru")

        assert_that(xml).contains('numerus="yes"')
        assert_that(xml).contains("<numerusform>%n файл</numerusform>")
        assert_that(xml).contains("<numerusform>%n файла</numerusform>")
        assert_that(xml).contains("<numerusform>%n файлов</numerusform>")

    def test_global_context(self) -> None:
        """Compile @default context."""
        entries = [
            TranslationEntry(
                context="@default",
                source="OK",
                disambiguation=None,
                note=None,
                translations={"fr": "OK"},
            )
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains("<name>@default</name>")

    def test_multiple_contexts(self) -> None:
        """Compile entries from multiple contexts."""
        entries = [
            TranslationEntry(
                context="LoginDialog",
                source="Username",
                disambiguation=None,
                note=None,
                translations={"fr": "Nom d'utilisateur"},
            ),
            TranslationEntry(
                context="MainWindow",
                source="Save",
                disambiguation=None,
                note=None,
                translations={"fr": "Enregistrer"},
            ),
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains("<name>LoginDialog</name>")
        assert_that(xml).contains("<name>MainWindow</name>")

    def test_skips_entries_without_language(self) -> None:
        """Entries without the target language are skipped."""
        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"de": "Hallo"},  # Only German
            )
        ]

        xml = compile_to_ts(entries, "fr")  # Request French

        # Should not contain the entry
        assert_that(xml).does_not_contain("<source>Hello</source>")

    def test_xml_escaping(self) -> None:
        """Special XML characters are escaped."""
        entries = [
            TranslationEntry(
                context="Test",
                source="A & B",
                disambiguation=None,
                note=None,
                translations={"fr": "A & B"},
            )
        ]

        xml = compile_to_ts(entries, "fr")

        assert_that(xml).contains("A &amp; B")

    def test_contexts_sorted(self) -> None:
        """Contexts are output in sorted order."""
        entries = [
            TranslationEntry(
                context="Zebra",
                source="Z",
                disambiguation=None,
                note=None,
                translations={"en": "Z"},
            ),
            TranslationEntry(
                context="Alpha",
                source="A",
                disambiguation=None,
                note=None,
                translations={"en": "A"},
            ),
        ]

        xml = compile_to_ts(entries, "en")

        # Alpha should come before Zebra
        alpha_pos = xml.find("Alpha")
        zebra_pos = xml.find("Zebra")
        assert_that(alpha_pos).is_less_than(zebra_pos)


class TestCompileTranslations:
    """Tests for compile_translations function."""

    def test_generates_ts_files(self, tmp_path: Path) -> None:
        """Generates .ts files for each language."""
        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"fr": "Bonjour", "de": "Hallo"},
            )
        ]

        output_files = compile_translations(entries, tmp_path)

        assert_that(output_files).is_length(2)
        assert_that((tmp_path / "de.ts").exists()).is_true()
        assert_that((tmp_path / "fr.ts").exists()).is_true()

    def test_respects_language_filter(self, tmp_path: Path) -> None:
        """Only specified languages are compiled."""
        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"fr": "Bonjour", "de": "Hallo", "ja": "こんにちは"},
            )
        ]

        output_files = compile_translations(entries, tmp_path, languages=["fr", "de"])

        assert_that(output_files).is_length(2)
        assert_that((tmp_path / "fr.ts").exists()).is_true()
        assert_that((tmp_path / "de.ts").exists()).is_true()
        assert_that((tmp_path / "ja.ts").exists()).is_false()

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Output directory is created if it doesn't exist."""
        output_dir = tmp_path / "nested" / "output"

        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"fr": "Bonjour"},
            )
        ]

        compile_translations(entries, output_dir)

        assert_that(output_dir.exists()).is_true()
        assert_that((output_dir / "fr.ts").exists()).is_true()

    def test_file_content_is_valid_xml(self, tmp_path: Path) -> None:
        """Generated files contain valid XML."""
        import xml.etree.ElementTree as ET

        entries = [
            TranslationEntry(
                context="Test",
                source="Hello",
                disambiguation=None,
                note=None,
                translations={"fr": "Bonjour"},
            )
        ]

        compile_translations(entries, tmp_path)

        # Read and parse the file
        content = (tmp_path / "fr.ts").read_text(encoding="utf-8")

        # Remove DOCTYPE (ET doesn't handle it well)
        xml_content = content.replace("<!DOCTYPE TS>\n", "")

        # Should parse without error
        ET.fromstring(xml_content)
