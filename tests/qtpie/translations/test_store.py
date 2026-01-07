"""Tests for the translation store."""

import pytest
from assertpy import assert_that

from qtpie.translations import (
    clear_bindings,
    clear_translations,
    get_binding_count,
    get_format_binding_count,
    get_language,
    load_translations_from_entries,
    lookup,
    lookup_plural,
    set_language,
)
from qtpie.translations.parser import TranslationEntry


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset translation state before each test."""
    clear_translations()
    clear_bindings()
    set_language("en")


class TestLanguage:
    """Tests for language setting."""

    def test_default_language_is_en(self) -> None:
        assert_that(get_language()).is_equal_to("en")

    def test_set_language(self) -> None:
        set_language("fr")
        assert_that(get_language()).is_equal_to("fr")


class TestLookup:
    """Tests for translation lookup."""

    def test_lookup_no_translation_returns_source(self) -> None:
        result = lookup("@default", "Hello")
        assert_that(result).is_equal_to("Hello")

    def test_lookup_with_translation(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        result = lookup("@default", "Hello")
        assert_that(result).is_equal_to("Bonjour")

    def test_lookup_with_disambiguation(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Open",
                disambiguation="file_menu",
                translations={"fr": "Ouvrir (fichier)"},
            ),
            TranslationEntry(
                context="@default",
                source="Open",
                disambiguation="edit_menu",
                translations={"fr": "Ouvrir (edition)"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        result1 = lookup("@default", "Open", "file_menu")
        result2 = lookup("@default", "Open", "edit_menu")

        assert_that(result1).is_equal_to("Ouvrir (fichier)")
        assert_that(result2).is_equal_to("Ouvrir (edition)")

    def test_lookup_fallback_to_default_context(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Global",
                translations={"fr": "Globale"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        # Lookup with specific context should fall back to @default
        result = lookup("MyWidget", "Global")
        assert_that(result).is_equal_to("Globale")

    def test_lookup_context_overrides_default(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="Title",
                translations={"fr": "Titre Global"},
            ),
            TranslationEntry(
                context="MyWidget",
                source="Title",
                translations={"fr": "Titre Widget"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        result = lookup("MyWidget", "Title")
        assert_that(result).is_equal_to("Titre Widget")


class TestLookupPlural:
    """Tests for plural translation lookup."""

    def test_lookup_plural_singular(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="%n item(s)",
                translations={"en": ["%n item", "%n items"]},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en")

        result = lookup_plural("@default", "%n item(s)", 1)
        assert_that(result).is_equal_to("1 item")

    def test_lookup_plural_multiple(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="%n item(s)",
                translations={"en": ["%n item", "%n items"]},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en")

        result = lookup_plural("@default", "%n item(s)", 5)
        assert_that(result).is_equal_to("5 items")

    def test_lookup_plural_replaces_n(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="%n file(s)",
                translations={"en": ["%n file", "%n files"]},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en")

        result = lookup_plural("@default", "%n file(s)", 42)
        assert_that(result).is_equal_to("42 files")

    def test_lookup_plural_no_translation_replaces_n(self) -> None:
        result = lookup_plural("@default", "%n item(s)", 3)
        assert_that(result).is_equal_to("3 item(s)")


class TestBindings:
    """Tests for translation bindings."""

    def test_binding_count_starts_at_zero(self) -> None:
        assert_that(get_binding_count()).is_equal_to(0)
        assert_that(get_format_binding_count()).is_equal_to(0)

    def test_clear_bindings_resets_count(self) -> None:
        clear_bindings()
        assert_that(get_binding_count()).is_equal_to(0)
