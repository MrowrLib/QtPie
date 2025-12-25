"""Tests for translation hot-reload functionality."""

import tempfile
from pathlib import Path

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

from qtpie import Widget, make, tr, widget
from qtpie.testing import QtDriver
from qtpie.translations.store import (
    clear_bindings,
    clear_translations,
    get_binding_count,
    get_language,
    load_translations_from_yaml,
    lookup,
    retranslate_all,
    set_language,
)
from qtpie.translations.translatable import enable_memory_store, is_memory_store_enabled


class TestTranslationStore:
    """Tests for the in-memory translation store."""

    def setup_method(self) -> None:
        """Reset store state before each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(False)

    def teardown_method(self) -> None:
        """Reset store state after each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(False)

    def test_set_and_get_language(self) -> None:
        """set_language and get_language work correctly."""
        set_language("fr")
        assert_that(get_language()).is_equal_to("fr")

        set_language("de")
        assert_that(get_language()).is_equal_to("de")

    def test_load_translations_from_yaml(self) -> None:
        """Translations can be loaded from YAML file."""
        yaml_content = """
TestWidget:
  Hello:
    fr: Bonjour
    de: Hallo
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            load_translations_from_yaml(yaml_path)

            set_language("fr")
            assert_that(lookup("TestWidget", "Hello")).is_equal_to("Bonjour")

            set_language("de")
            assert_that(lookup("TestWidget", "Hello")).is_equal_to("Hallo")
        finally:
            yaml_path.unlink()

    def test_lookup_returns_source_if_no_translation(self) -> None:
        """lookup returns source text if no translation found."""
        set_language("fr")
        assert_that(lookup("TestWidget", "Unknown")).is_equal_to("Unknown")

    def test_lookup_returns_source_if_wrong_language(self) -> None:
        """lookup returns source if translation not available for language."""
        yaml_content = """
TestWidget:
  Hello:
    fr: Bonjour
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            load_translations_from_yaml(yaml_path)
            set_language("de")  # German not available
            assert_that(lookup("TestWidget", "Hello")).is_equal_to("Hello")
        finally:
            yaml_path.unlink()

    def test_enable_memory_store(self) -> None:
        """enable_memory_store toggles the memory store mode."""
        assert_that(is_memory_store_enabled()).is_false()

        enable_memory_store(True)
        assert_that(is_memory_store_enabled()).is_true()

        enable_memory_store(False)
        assert_that(is_memory_store_enabled()).is_false()


class TestBindingRegistry:
    """Tests for translation binding registration."""

    def setup_method(self) -> None:
        """Reset store state before each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(True)

    def teardown_method(self) -> None:
        """Reset store state after each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(False)

    def test_make_registers_bindings(self, qt: QtDriver) -> None:
        """make() with tr[] registers translation bindings."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, text=tr["Hello"])

        w = TestWidget()
        qt.track(w)

        # Should have registered one binding
        assert_that(get_binding_count()).is_greater_than(0)

    def test_multiple_tr_kwargs_register_multiple_bindings(self, qt: QtDriver) -> None:
        """Multiple tr[] kwargs register multiple bindings."""
        clear_bindings()

        @widget()
        class TestWidget(QWidget, Widget):
            button: QPushButton = make(
                QPushButton,
                text=tr["Save"],
                toolTip=tr["Save changes"],
            )

        w = TestWidget()
        qt.track(w)

        # Should have registered two bindings (text and toolTip)
        assert_that(get_binding_count()).is_equal_to(2)


class TestRetranslation:
    """Tests for retranslating widgets."""

    def setup_method(self) -> None:
        """Reset store state before each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(True)

    def teardown_method(self) -> None:
        """Reset store state after each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(False)

    def test_retranslate_all_updates_widget_text(self, qt: QtDriver) -> None:
        """retranslate_all() updates widget text via setProperty."""
        # Load translations
        yaml_content = """
TestWidget:
  Hello:
    fr: Bonjour
    de: Hallo
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            load_translations_from_yaml(yaml_path)
            set_language("en")

            @widget()
            class TestWidget(QWidget, Widget):
                label: QLabel = make(QLabel, text=tr["Hello"])

            w = TestWidget()
            qt.track(w)

            # Initially shows source text (no English translation)
            assert_that(w.label.text()).is_equal_to("Hello")

            # Change language and retranslate
            set_language("fr")
            retranslate_all()

            # Now shows French translation
            assert_that(w.label.text()).is_equal_to("Bonjour")

            # Change to German
            set_language("de")
            retranslate_all()

            assert_that(w.label.text()).is_equal_to("Hallo")
        finally:
            yaml_path.unlink()

    def test_retranslate_updates_multiple_properties(self, qt: QtDriver) -> None:
        """retranslate_all() updates multiple properties on same widget."""
        yaml_content = """
TestWidget:
  Save:
    fr: Sauvegarder
  "Save changes":
    fr: Sauvegarder les modifications
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            load_translations_from_yaml(yaml_path)
            set_language("en")

            @widget()
            class TestWidget(QWidget, Widget):
                button: QPushButton = make(
                    QPushButton,
                    text=tr["Save"],
                    toolTip=tr["Save changes"],
                )

            w = TestWidget()
            qt.track(w)

            # Change to French and retranslate
            set_language("fr")
            retranslate_all()

            assert_that(w.button.text()).is_equal_to("Sauvegarder")
            assert_that(w.button.toolTip()).is_equal_to("Sauvegarder les modifications")
        finally:
            yaml_path.unlink()

    def test_retranslate_handles_deleted_widgets(self, qt: QtDriver) -> None:
        """retranslate_all() doesn't crash when widgets have been deleted."""
        import gc

        yaml_content = """
TestWidget:
  Hello:
    fr: Bonjour
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            load_translations_from_yaml(yaml_path)
            set_language("en")

            @widget()
            class TestWidget(QWidget, Widget):
                label: QLabel = make(QLabel, text=tr["Hello"])

            w = TestWidget()
            initial_count = get_binding_count()
            assert_that(initial_count).is_greater_than(0)

            # Delete the widget and force garbage collection
            del w
            gc.collect()

            # Retranslate should not crash even with dead weak references
            set_language("fr")
            retranslate_all()

            # After retranslate, dead bindings should be cleaned up
            # The count should be 0 since the widget was garbage collected
            assert_that(get_binding_count()).is_equal_to(0)
        finally:
            yaml_path.unlink()


class TestTranslatableResolveWithMemoryStore:
    """Tests for Translatable.resolve() with memory store."""

    def setup_method(self) -> None:
        """Reset store state before each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(True)

    def teardown_method(self) -> None:
        """Reset store state after each test."""
        clear_bindings()
        clear_translations()
        enable_memory_store(False)

    def test_tr_resolve_uses_memory_store(self, qt: QtDriver) -> None:
        """tr[] resolves from memory store when enabled."""
        yaml_content = """
TestWidget:
  Greeting:
    fr: Salut
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            yaml_path = Path(f.name)

        try:
            load_translations_from_yaml(yaml_path)
            set_language("fr")

            @widget()
            class TestWidget(QWidget, Widget):
                label: QLabel = make(QLabel, text=tr["Greeting"])

            w = TestWidget()
            qt.track(w)

            # Should use French translation from memory store
            assert_that(w.label.text()).is_equal_to("Salut")
        finally:
            yaml_path.unlink()
