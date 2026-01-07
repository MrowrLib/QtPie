"""Integration tests for translations with widgets."""

import tempfile
from pathlib import Path

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import Widget, entrypoint, new, t, widget
from qtpie.testing import QtDriver
from qtpie.translations import (
    clear_bindings,
    clear_translations,
    enable_memory_store,
    load_translations_from_entries,
    set_language,
)
from qtpie.translations.parser import TranslationEntry


@pytest.fixture(autouse=True)
def reset_translations() -> None:
    """Reset translation state before each test."""
    clear_translations()
    clear_bindings()
    enable_memory_store(True)
    set_language("en")


class TestTranslationsWithWidgets:
    """Tests for t() used with widgets."""

    def test_t_with_qlabel(self, qt: QtDriver) -> None:
        """t() works as first argument to new() for QLabel."""

        @widget
        class TestWidget(Widget):
            label: QLabel = new(t("Hello"))

        w = TestWidget()
        qt.track(w)

        # Without translation, shows source text
        assert_that(w.label.text()).is_equal_to("Hello")

    def test_t_with_translation_loaded(self, qt: QtDriver) -> None:
        """t() resolves to translated text when translations are loaded."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @widget
        class TestWidget(Widget):
            label: QLabel = new(t("Hello"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Bonjour")

    def test_t_with_disambiguation(self, qt: QtDriver) -> None:
        """t() with context= for disambiguation."""
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
                disambiguation="file",
                translations={"fr": "Ouvrir (fichier)"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @widget
        class TestWidget(Widget):
            menu_open: QLabel = new(t("Open", context="menu"))
            file_open: QLabel = new(t("Open", context="file"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.menu_open.text()).is_equal_to("Ouvrir (menu)")
        assert_that(w.file_open.text()).is_equal_to("Ouvrir (fichier)")

    def test_t_with_widget_context(self, qt: QtDriver) -> None:
        """t() uses widget class name as translation context."""
        entries = [
            TranslationEntry(
                context="MyCustomWidget",
                source="Title",
                translations={"fr": "Titre personnalisé"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @widget
        class MyCustomWidget(Widget):
            label: QLabel = new(t("Title"))

        w = MyCustomWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Titre personnalisé")

    def test_t_falls_back_to_global(self, qt: QtDriver) -> None:
        """t() falls back to @default context if widget context has no match."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Global Text",
                translations={"fr": "Texte global"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @widget
        class AnyWidget(Widget):
            label: QLabel = new(t("Global Text"))

        w = AnyWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Texte global")

    def test_t_with_button(self, qt: QtDriver) -> None:
        """t() works with QPushButton."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Click Me",
                translations={"de": "Klick mich"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("de")

        @widget
        class TestWidget(Widget):
            button: QPushButton = new(t("Click Me"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.button.text()).is_equal_to("Klick mich")

    def test_t_no_translation_returns_source(self, qt: QtDriver) -> None:
        """t() returns source text when no translation exists."""
        set_language("fr")  # No translations loaded

        @widget
        class TestWidget(Widget):
            label: QLabel = new(t("Untranslated"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Untranslated")

    def test_multiple_t_in_same_widget(self, qt: QtDriver) -> None:
        """Multiple t() calls in the same widget work correctly."""
        entries = [
            TranslationEntry(
                context="@default",
                source="First",
                translations={"es": "Primero"},
            ),
            TranslationEntry(
                context="@default",
                source="Second",
                translations={"es": "Segundo"},
            ),
            TranslationEntry(
                context="@default",
                source="Third",
                translations={"es": "Tercero"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("es")

        @widget
        class TestWidget(Widget):
            first: QLabel = new(t("First"))
            second: QLabel = new(t("Second"))
            third: QLabel = new(t("Third"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.first.text()).is_equal_to("Primero")
        assert_that(w.second.text()).is_equal_to("Segundo")
        assert_that(w.third.text()).is_equal_to("Tercero")

    def test_set_language_retranslates_widgets(self, qt: QtDriver) -> None:
        """set_language() automatically retranslates bound widgets."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"en": "Hello", "fr": "Bonjour", "de": "Hallo"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)  # Start with English

        @widget
        class TestWidget(Widget):
            label: QLabel = new(t("Hello"))

        w = TestWidget()
        qt.track(w)

        # Initially English
        assert_that(w.label.text()).is_equal_to("Hello")

        # Change to French - should auto-retranslate
        set_language("fr")
        assert_that(w.label.text()).is_equal_to("Bonjour")

        # Change to German - should auto-retranslate again
        set_language("de")
        assert_that(w.label.text()).is_equal_to("Hallo")

    def test_set_language_no_change_skips_retranslate(self, qt: QtDriver) -> None:
        """set_language() with same language doesn't retranslate."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"fr": "Bonjour"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr", retranslate=False)

        @widget
        class TestWidget(Widget):
            label: QLabel = new(t("Hello"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Bonjour")

        # Calling with same language should be a no-op
        set_language("fr")
        assert_that(w.label.text()).is_equal_to("Bonjour")


class TestEntrypointWithTranslations:
    """Tests for @entrypoint with translation options.

    Note: @entrypoint only stores config - translations are loaded when the
    app actually runs. These tests verify the config is stored correctly and
    that the translation loading works when triggered manually.
    """

    def test_entrypoint_stores_translations_config(self) -> None:
        """@entrypoint(translations=...) stores translation config."""
        from qtpie.entrypoint import ENTRY_CONFIG_ATTR

        @entrypoint(translations="app.yml", language="fr")
        @widget
        class TestApp(Widget):
            label: QLabel = new(t("Hello"))

        config = getattr(TestApp, ENTRY_CONFIG_ATTR)
        assert_that(config.translations).is_equal_to("app.yml")
        assert_that(config.language).is_equal_to("fr")

    def test_entrypoint_stores_multiple_translations(self) -> None:
        """@entrypoint(translations=[...]) stores list of paths."""
        from qtpie.entrypoint import ENTRY_CONFIG_ATTR

        @entrypoint(translations=["a.yml", "b.yml"], language="de")
        @widget
        class TestApp(Widget):
            label: QLabel = new(t("Hello"))

        config = getattr(TestApp, ENTRY_CONFIG_ATTR)
        assert_that(config.translations).is_equal_to(("a.yml", "b.yml"))

    def test_entrypoint_stores_watch_translations(self) -> None:
        """@entrypoint(watch_translations=True) stores watch config."""
        from qtpie.entrypoint import ENTRY_CONFIG_ATTR

        @entrypoint(translations="app.yml", watch_translations=True)
        @widget
        class TestApp(Widget):
            label: QLabel = new(t("Hello"))

        config = getattr(TestApp, ENTRY_CONFIG_ATTR)
        assert_that(config.watch_translations).is_true()

    def test_entrypoint_default_language_is_english(self) -> None:
        """@entrypoint defaults to language='en'."""
        from qtpie.entrypoint import ENTRY_CONFIG_ATTR

        @entrypoint(translations="app.yml")
        @widget
        class TestApp(Widget):
            label: QLabel = new(t("Hello"))

        config = getattr(TestApp, ENTRY_CONFIG_ATTR)
        assert_that(config.language).is_equal_to("en")

    def test_translations_load_and_apply(self, qt: QtDriver) -> None:
        """Translations load from YAML and apply to widgets."""
        # This tests the full flow by manually loading translations
        # (simulating what @entrypoint does when the app runs)
        yaml_content = """
:global:
    Hello:
        fr: Bonjour
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            yaml_path = Path(f.name)

        try:
            from qtpie.translations import load_translations_from_yaml

            # Simulate what @entrypoint does when the app runs
            load_translations_from_yaml(str(yaml_path))
            set_language("fr")

            @widget
            class TestApp(Widget):
                label: QLabel = new(t("Hello"))

            w = TestApp()
            qt.track(w)

            assert_that(w.label.text()).is_equal_to("Bonjour")
        finally:
            yaml_path.unlink()

    def test_entrypoint_without_translations(self, qt: QtDriver) -> None:
        """@entrypoint without translations= still works, t() returns source."""

        @entrypoint
        @widget
        class TestApp(Widget):
            label: QLabel = new(t("No Translation"))

        w = TestApp()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("No Translation")
