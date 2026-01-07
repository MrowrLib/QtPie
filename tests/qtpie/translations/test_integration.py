# pyright: reportPrivateUsage=false
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


class TestTranslatableInFormLayout:
    """Tests for t() used with label= in form layouts."""

    def test_label_t_in_form_layout(self, qt: QtDriver) -> None:
        """label=t() works in form layouts."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QLineEdit

        entries = [
            TranslationEntry(
                context="@default",
                source="Name",
                translations={"fr": "Nom"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @dataclass
        class Person:
            name: str = ""

        @widget(layout="form", record=Person())
        class FormWidget(Widget[Person]):
            name: QLineEdit = new(label=t("Name"))

        w = FormWidget()
        qt.track(w)

        # Check that the widget was created and added to layout
        layout = w.layout()
        assert layout is not None

        # The label should be translated
        from PySide6.QtWidgets import QFormLayout

        assert isinstance(layout, QFormLayout)
        # Get the label for the first row
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        label_widget = label_item.widget()
        assert label_widget is not None
        assert isinstance(label_widget, QLabel)
        assert_that(label_widget.text()).is_equal_to("Nom")

    def test_label_t_retranslates_on_language_change(self, qt: QtDriver) -> None:
        """label=t() retranslates when language changes."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QFormLayout, QLineEdit

        entries = [
            TranslationEntry(
                context="@default",
                source="Username",
                translations={"en": "Username", "fr": "Nom d'utilisateur", "de": "Benutzername"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        @dataclass
        class User:
            username: str = ""

        @widget(layout="form", record=User())
        class UserForm(Widget[User]):
            username: QLineEdit = new(label=t("Username"))

        w = UserForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)
        label_widget = layout.labelForField(w.username)
        assert label_widget is not None
        assert isinstance(label_widget, QLabel)

        # Initially English
        assert_that(label_widget.text()).is_equal_to("Username")

        # Change to French - should retranslate
        set_language("fr")
        assert_that(label_widget.text()).is_equal_to("Nom d'utilisateur")

        # Change to German - should retranslate again
        set_language("de")
        assert_that(label_widget.text()).is_equal_to("Benutzername")

    def test_label_t_without_translation(self, qt: QtDriver) -> None:
        """label=t() shows source text when no translation exists."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit

        @dataclass
        class Person:
            name: str = ""

        @widget(layout="form", record=Person())
        class FormWidget(Widget[Person]):
            name: QLineEdit = new(label=t("Username"))

        w = FormWidget()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        label_widget = label_item.widget()
        assert label_widget is not None
        assert isinstance(label_widget, QLabel)
        assert_that(label_widget.text()).is_equal_to("Username")


class TestTranslatableWithBind:
    """Tests for t() used with bind= for format string bindings."""

    def test_bind_t_with_format_string(self, qt: QtDriver) -> None:
        """bind=t() with format string resolves and binds correctly."""
        from dataclasses import dataclass

        entries = [
            TranslationEntry(
                context="@default",
                source="Name: {name}",
                translations={"fr": "Nom: {name}"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @dataclass
        class Person:
            name: str = "Alice"

        @widget(record=Person())
        class BindWidget(Widget[Person]):
            info: QLabel = new(bind=t("Name: {name}"))

        w = BindWidget()
        qt.track(w)

        # The label should show the translated format with record value
        assert_that(w.info.text()).is_equal_to("Nom: Alice")

    def test_bind_t_without_translation(self, qt: QtDriver) -> None:
        """bind=t() shows source text format when no translation exists."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = "Bob"

        @widget(record=Person())
        class BindWidget(Widget[Person]):
            info: QLabel = new(bind=t("Hello {name}!"))

        w = BindWidget()
        qt.track(w)

        assert_that(w.info.text()).is_equal_to("Hello Bob!")

    def test_bind_t_retranslates_on_language_change(self, qt: QtDriver) -> None:
        """bind=t() retranslates when language changes."""
        from dataclasses import dataclass

        entries = [
            TranslationEntry(
                context="@default",
                source="Hello {name}!",
                translations={
                    "en": "Hello {name}!",
                    "fr": "Bonjour {name}!",
                    "de": "Hallo {name}!",
                },
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        @dataclass
        class Person:
            name: str = "Alice"

        @widget(record=Person())
        class GreetingWidget(Widget[Person]):
            greeting: QLabel = new(bind=t("Hello {name}!"))

        w = GreetingWidget()
        qt.track(w)

        # Initially English
        assert_that(w.greeting.text()).is_equal_to("Hello Alice!")

        # Change to French - should retranslate
        set_language("fr")
        assert_that(w.greeting.text()).is_equal_to("Bonjour Alice!")

        # Change to German - should retranslate again
        set_language("de")
        assert_that(w.greeting.text()).is_equal_to("Hallo Alice!")


class TestTranslatableRetranslation:
    """Tests for retranslation when language changes."""

    def test_retranslate_positional_arg(self, qt: QtDriver) -> None:
        """Positional t() args retranslate when language changes."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Submit",
                translations={"en": "Submit", "fr": "Soumettre", "de": "Absenden"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        @widget
        class TestWidget(Widget):
            btn: QPushButton = new(t("Submit"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.btn.text()).is_equal_to("Submit")

        set_language("fr")
        assert_that(w.btn.text()).is_equal_to("Soumettre")

        set_language("de")
        assert_that(w.btn.text()).is_equal_to("Absenden")

    def test_retranslate_multiple_widgets(self, qt: QtDriver) -> None:
        """Multiple widgets retranslate together."""
        entries = [
            TranslationEntry(
                context="@default",
                source="Save",
                translations={"en": "Save", "fr": "Enregistrer"},
            ),
            TranslationEntry(
                context="@default",
                source="Cancel",
                translations={"en": "Cancel", "fr": "Annuler"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        @widget
        class TestWidget(Widget):
            save_btn: QPushButton = new(t("Save"))
            cancel_btn: QPushButton = new(t("Cancel"))

        w = TestWidget()
        qt.track(w)

        assert_that(w.save_btn.text()).is_equal_to("Save")
        assert_that(w.cancel_btn.text()).is_equal_to("Cancel")

        set_language("fr")
        assert_that(w.save_btn.text()).is_equal_to("Enregistrer")
        assert_that(w.cancel_btn.text()).is_equal_to("Annuler")


class TestTranslatableComplex:
    """Complex tests combining multiple t() features."""

    def test_full_widget_with_translations(self, qt: QtDriver) -> None:
        """Widget with t() in positional args, labels, and buttons."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit

        entries = [
            TranslationEntry(
                context="@default",
                source="Dog's Name",
                translations={"fr": "Nom du chien"},
            ),
            TranslationEntry(
                context="@default",
                source="Save",
                translations={"fr": "Enregistrer"},
            ),
            TranslationEntry(
                context="@default",
                source="Info",
                translations={"fr": "Info"},
            ),
        ]
        load_translations_from_entries(entries)
        set_language("fr")

        @dataclass
        class Dog:
            name: str = "Fido"

        @widget(layout="form", record=Dog())
        class DogEditor(Widget[Dog]):
            name: QLineEdit = new(label=t("Dog's Name"))
            info_label: QLabel = new(t("Info"), label=t("Info"))
            save_btn: QPushButton = new(t("Save"), label=t("Save"))

        w = DogEditor()
        qt.track(w)

        # Check button text
        assert_that(w.save_btn.text()).is_equal_to("Enregistrer")

        # Check info label text
        assert_that(w.info_label.text()).is_equal_to("Info")

        # Check form layout label
        layout = w.layout()
        assert isinstance(layout, QFormLayout)
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        label_widget = label_item.widget()
        assert label_widget is not None
        assert isinstance(label_widget, QLabel)
        assert_that(label_widget.text()).is_equal_to("Nom du chien")


class TestNonQtObjectRetranslation:
    """Tests for retranslation of non-Qt objects with t()."""

    def test_retranslate_with_setXxx_method(self) -> None:
        """Retranslation works for objects with setXxx() methods."""
        from qtpie.translations import (
            clear_bindings,
            clear_translations,
            enable_memory_store,
            load_translations_from_entries,
            register_binding,
            set_language,
        )

        clear_translations()
        clear_bindings()
        enable_memory_store(True)

        entries = [
            TranslationEntry(
                context="@default",
                source="Hello",
                translations={"en": "Hello", "fr": "Bonjour"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        # Non-Qt object with setXxx() method
        class MyObject:
            def __init__(self) -> None:
                self._text = ""

            def setText(self, value: str) -> None:
                self._text = value

            def getText(self) -> str:
                return self._text

        obj = MyObject()
        obj.setText("Hello")

        # Register binding
        register_binding(obj, "text", "Hello")

        assert_that(obj.getText()).is_equal_to("Hello")

        # Change language and retranslate
        set_language("fr")
        assert_that(obj.getText()).is_equal_to("Bonjour")

    def test_retranslate_with_property_setter(self) -> None:
        """Retranslation works for objects with property setters."""
        from qtpie.translations import (
            clear_bindings,
            clear_translations,
            enable_memory_store,
            load_translations_from_entries,
            register_binding,
            set_language,
        )

        clear_translations()
        clear_bindings()
        enable_memory_store(True)

        entries = [
            TranslationEntry(
                context="@default",
                source="Goodbye",
                translations={"en": "Goodbye", "fr": "Au revoir"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        # Non-Qt object with property setter
        class MyObject:
            def __init__(self) -> None:
                self._message = ""

            @property
            def message(self) -> str:
                return self._message

            @message.setter
            def message(self, value: str) -> None:
                self._message = value

        obj = MyObject()
        obj.message = "Goodbye"

        # Register binding
        register_binding(obj, "message", "Goodbye")

        assert_that(obj.message).is_equal_to("Goodbye")

        # Change language and retranslate
        set_language("fr")
        assert_that(obj.message).is_equal_to("Au revoir")

    def test_retranslate_no_setter_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Retranslation logs warning when no setter is available."""
        import logging

        from qtpie.translations import (
            clear_bindings,
            clear_translations,
            enable_memory_store,
            load_translations_from_entries,
            register_binding,
            set_language,
        )

        clear_translations()
        clear_bindings()
        enable_memory_store(True)

        entries = [
            TranslationEntry(
                context="@default",
                source="ImmutableText",
                translations={"en": "ImmutableText", "fr": "TexteImmuable"},
            )
        ]
        load_translations_from_entries(entries)
        set_language("en", retranslate=False)

        # Non-Qt object with no setter (constructor-only argument)
        class ImmutableObject:
            def __init__(self, readonly: str) -> None:
                self._readonly = readonly

            @property
            def readonly(self) -> str:
                return self._readonly

            # No setter! Property is read-only

        obj = ImmutableObject("ImmutableText")

        # Register binding (will fail to retranslate)
        register_binding(obj, "readonly", "ImmutableText")

        # Change language - should log warning
        with caplog.at_level(logging.WARNING):
            set_language("fr")

        # The value should NOT have changed (no setter available)
        assert_that(obj.readonly).is_equal_to("ImmutableText")

        # Check that warning was logged
        assert_that(len(caplog.records)).is_greater_than(0)
        assert_that(caplog.records[-1].message).contains("readonly")
        assert_that(caplog.records[-1].message).contains("no setter found")

    def test_set_property_value_tries_setXxx_first(self) -> None:
        """_set_property_value tries setXxx() method before direct assignment."""
        from qtpie.translations.store import _set_property_value

        call_order: list[str] = []

        class OrderTestObject:
            def __init__(self) -> None:
                self._value = ""

            @property
            def value(self) -> str:
                return self._value

            @value.setter
            def value(self, v: str) -> None:
                call_order.append("property")
                self._value = v

            def setValue(self, v: str) -> None:
                call_order.append("setXxx")
                self._value = v

        obj = OrderTestObject()
        _set_property_value(obj, "value", "test")

        # setXxx() should be called first
        assert_that(call_order).is_equal_to(["setXxx"])
        assert_that(obj.value).is_equal_to("test")
