"""Tests for the .ts compiler."""

import tempfile
from pathlib import Path

from assertpy import assert_that

from qtpie.translations import compile_to_ts, compile_translations, get_all_languages
from qtpie.translations.parser import TranslationEntry


class TestCompileToTs:
    """Tests for compiling to .ts XML format."""

    def test_compile_simple(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour"},
            )
        ]
        result = compile_to_ts(entries, "fr")

        assert_that(result).contains('<?xml version="1.0" encoding="utf-8"?>')
        assert_that(result).contains('<TS version="2.1" language="fr">')
        assert_that(result).contains("<source>Hello</source>")
        assert_that(result).contains("<translation>Bonjour</translation>")

    def test_compile_with_context(self) -> None:
        entries = [
            TranslationEntry(
                context="MyWidget",
                source="Title",
                translations={"fr": "Titre"},
            )
        ]
        result = compile_to_ts(entries, "fr")

        assert_that(result).contains("<context>")
        assert_that(result).contains("<name>MyWidget</name>")

    def test_compile_with_disambiguation(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Open",
                disambiguation="file_menu",
                translations={"fr": "Ouvrir"},
            )
        ]
        result = compile_to_ts(entries, "fr")

        assert_that(result).contains("<comment>file_menu</comment>")

    def test_compile_with_note(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Submit",
                note="For form submission",
                translations={"fr": "Soumettre"},
            )
        ]
        result = compile_to_ts(entries, "fr")

        assert_that(result).contains("<extracomment>For form submission</extracomment>")

    def test_compile_plural(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="%n file(s)",
                translations={"fr": ["%n fichier", "%n fichiers"]},
            )
        ]
        result = compile_to_ts(entries, "fr")

        assert_that(result).contains('numerus="yes"')
        assert_that(result).contains("<numerusform>%n fichier</numerusform>")
        assert_that(result).contains("<numerusform>%n fichiers</numerusform>")


class TestGetAllLanguages:
    """Tests for extracting languages from entries."""

    def test_single_language(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour"},
            )
        ]
        languages = get_all_languages(entries)
        assert_that(languages).is_equal_to({"fr"})

    def test_multiple_languages(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour", "de": "Hallo", "es": "Hola"},
            )
        ]
        languages = get_all_languages(entries)
        assert_that(languages).is_equal_to({"fr", "de", "es"})

    def test_no_languages(self) -> None:
        entries: list[TranslationEntry] = []
        languages = get_all_languages(entries)
        assert_that(languages).is_empty()


class TestCompileTranslations:
    """Tests for compiling to .ts files on disk."""

    def test_compile_creates_files(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour", "de": "Hallo"},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = compile_translations(entries, output_dir)

            assert_that(files).is_length(2)
            assert_that((output_dir / "de.ts").exists()).is_true()
            assert_that((output_dir / "fr.ts").exists()).is_true()

    def test_compile_specific_languages(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour", "de": "Hallo", "es": "Hola"},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            files = compile_translations(entries, output_dir, languages=["fr"])

            assert_that(files).is_length(1)
            assert_that((output_dir / "fr.ts").exists()).is_true()
            assert_that((output_dir / "de.ts").exists()).is_false()
