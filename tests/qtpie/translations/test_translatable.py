"""Tests for the t() function and Translatable class."""

import pytest
from assertpy import assert_that

from qtpie.translations import (
    Translatable,
    clear_translations,
    enable_memory_store,
    get_translation_context,
    load_translations_from_entries,
    set_language,
    set_translation_context,
    t,
)
from qtpie.translations.parser import TranslationEntry


@pytest.fixture(autouse=True)
def reset_translations() -> None:
    """Reset translation state before each test."""
    clear_translations()
    enable_memory_store(True)
    set_language("en")


class TestTFunction:
    """Tests for the t() function."""

    def test_t_returns_translatable(self) -> None:
        result = t("Hello")
        assert_that(result).is_instance_of(Translatable)

    def test_t_stores_text(self) -> None:
        result = t("Hello World")
        assert_that(result.text).is_equal_to("Hello World")

    def test_t_with_context(self) -> None:
        result = t("Open", context="menu")
        assert_that(result.text).is_equal_to("Open")
        assert_that(result.context).is_equal_to("menu")

    def test_t_default_context_is_none(self) -> None:
        result = t("Hello")
        assert_that(result.context).is_none()


class TestTranslatableResolve:
    """Tests for resolving Translatable to translated text."""

    def test_resolve_without_translation_returns_source(self) -> None:
        marker = t("Hello")
        result = marker.resolve()
        assert_that(result).is_equal_to("Hello")

    def test_resolve_with_translation(self) -> None:
        # Load translation
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        marker = t("Hello")
        result = marker.resolve()
        assert_that(result).is_equal_to("Bonjour")

    def test_resolve_with_context(self) -> None:
        # Load translations with disambiguation
        entries = [
            TranslationEntry(
                context="@default",
                source="Open",
                disambiguation="menu",
                translations={"fr": "Ouvrir (menu)"},
            ),
            TranslationEntry(
                context="@default",
                source="Open",
                disambiguation="action",
                translations={"fr": "Ouvrir (action)"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        marker = t("Open", context="menu")
        result = marker.resolve()
        assert_that(result).is_equal_to("Ouvrir (menu)")

    def test_resolve_uses_widget_context(self) -> None:
        # Load translation with widget context
        entries = [
            TranslationEntry(
                context="MyWidget",
                source="Title",
                translations={"fr": "Titre (MyWidget)"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        set_translation_context("MyWidget")
        marker = t("Title")
        result = marker.resolve()
        assert_that(result).is_equal_to("Titre (MyWidget)")


class TestTranslatablePlural:
    """Tests for plural support."""

    def test_plural_with_count(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="%n file(s)",
                translations={"en": ["%n file", "%n files"]},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en")

        marker = t("%n file(s)")

        # Singular
        result = marker(1)
        assert_that(result).is_equal_to("1 file")

        # Plural
        result = marker(5)
        assert_that(result).is_equal_to("5 files")

    def test_plural_zero(self) -> None:
        entries = [
            TranslationEntry(
                context="@default",
                source="%n item(s)",
                translations={"en": ["%n item", "%n items"]},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en")

        marker = t("%n item(s)")
        result = marker(0)
        assert_that(result).is_equal_to("0 items")


class TestTranslationContext:
    """Tests for translation context management."""

    def test_set_translation_context(self) -> None:
        set_translation_context("TestWidget")
        assert_that(get_translation_context()).is_equal_to("TestWidget")

    def test_default_context(self) -> None:
        # Reset to default
        set_translation_context("")
        assert_that(get_translation_context()).is_equal_to("")


class TestTranslatableHashable:
    """Tests that Translatable is hashable (frozen dataclass)."""

    def test_translatable_is_hashable(self) -> None:
        marker = t("Hello")
        # Should not raise
        hash(marker)

    def test_translatable_equality(self) -> None:
        a = t("Hello")
        b = t("Hello")
        assert_that(a).is_equal_to(b)

    def test_translatable_with_context_equality(self) -> None:
        a = t("Open", context="menu")
        b = t("Open", context="menu")
        c = t("Open", context="action")
        assert_that(a).is_equal_to(b)
        assert_that(a).is_not_equal_to(c)
