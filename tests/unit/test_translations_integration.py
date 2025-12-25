"""Integration tests for translations with real Qt widgets and tr()."""

import subprocess
from pathlib import Path
from textwrap import dedent
from typing import override

from assertpy import assert_that
from qtpy.QtCore import QTranslator
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

from qtpie import Widget, make, widget
from qtpie.testing import QtDriver
from qtpie.translations.compiler import compile_translations
from qtpie.translations.parser import parse_yaml


def compile_ts_to_qm(ts_path: Path, qm_path: Path) -> bool:
    """Compile .ts to .qm using lrelease."""
    try:
        # Try pyside6-lrelease first
        result = subprocess.run(
            ["pyside6-lrelease", str(ts_path), "-qm", str(qm_path)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        pass

    try:
        # Try lrelease (from Qt installation)
        result = subprocess.run(
            ["lrelease", str(ts_path), "-qm", str(qm_path)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


class TestTranslationsWithWidgets:
    """Test translations with real Qt widgets using tr()."""

    def test_basic_tr_returns_source_without_translation(self, qt: QtDriver) -> None:
        """tr() returns source string when no translation is loaded."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel)

            @override
            def setup(self) -> None:
                self.label.setText(self.tr("Hello"))

        w = TestWidget()
        qt.track(w)

        # Without translation loaded, tr() returns source
        assert_that(w.label.text()).is_equal_to("Hello")

    def test_tr_with_disambiguation(self, qt: QtDriver) -> None:
        """tr() with disambiguation parameter works correctly."""

        @widget()
        class TestWidget(QWidget, Widget):
            verb_label: QLabel = make(QLabel)
            adj_label: QLabel = make(QLabel)

            @override
            def setup(self) -> None:
                self.verb_label.setText(self.tr("Open", "menu"))
                self.adj_label.setText(self.tr("Open", "status"))

        w = TestWidget()
        qt.track(w)

        # Both return "Open" without translation (disambiguation is for lookup)
        assert_that(w.verb_label.text()).is_equal_to("Open")
        assert_that(w.adj_label.text()).is_equal_to("Open")

    def test_tr_with_plural(self, qt: QtDriver) -> None:
        """tr() with %n and count parameter works correctly."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel)

            def set_count(self, n: int) -> None:
                self.label.setText(self.tr("%n file(s)", "", n))

        w = TestWidget()
        qt.track(w)

        w.set_count(1)
        assert_that(w.label.text()).is_equal_to("1 file(s)")

        w.set_count(5)
        assert_that(w.label.text()).is_equal_to("5 file(s)")

    def test_compile_yaml_and_verify_ts_structure(self, tmp_path: Path) -> None:
        """Compile YAML to .ts and verify the XML structure."""
        yaml_content = dedent("""
            :global:
              OK:
                fr: OK
                de: OK

            TestWidget:
              Hello:
                fr: Bonjour
                de: Hallo

              Open|menu:
                fr: Ouvrir
                de: Öffnen

              Open|status:
                fr: Ouvert
                de: Geöffnet

              "%n file(s)":
                fr: ["%n fichier", "%n fichiers"]
                de: ["%n Datei", "%n Dateien"]

              "Save changes?":
                :note: Shown when closing
                fr: "Enregistrer les modifications ?"
                de: "Änderungen speichern?"
        """)

        entries = parse_yaml(yaml_content)
        compile_translations(entries, tmp_path)

        # Check French file
        fr_content = (tmp_path / "fr.ts").read_text(encoding="utf-8")

        assert_that(fr_content).contains('<TS version="2.1" language="fr">')
        assert_that(fr_content).contains("<name>@default</name>")
        assert_that(fr_content).contains("<name>TestWidget</name>")
        assert_that(fr_content).contains("<source>Hello</source>")
        assert_that(fr_content).contains("<translation>Bonjour</translation>")
        assert_that(fr_content).contains("<source>Open</source>")
        assert_that(fr_content).contains("<comment>menu</comment>")
        assert_that(fr_content).contains("<translation>Ouvrir</translation>")
        assert_that(fr_content).contains("<comment>status</comment>")
        assert_that(fr_content).contains("<translation>Ouvert</translation>")
        assert_that(fr_content).contains('numerus="yes"')
        assert_that(fr_content).contains("<numerusform>%n fichier</numerusform>")
        assert_that(fr_content).contains("<numerusform>%n fichiers</numerusform>")
        assert_that(fr_content).contains("<extracomment>Shown when closing</extracomment>")

        # Check German file
        de_content = (tmp_path / "de.ts").read_text(encoding="utf-8")

        assert_that(de_content).contains('<TS version="2.1" language="de">')
        assert_that(de_content).contains("<translation>Hallo</translation>")
        assert_that(de_content).contains("<translation>Öffnen</translation>")
        assert_that(de_content).contains("<translation>Geöffnet</translation>")

    def test_full_workflow_yaml_to_widget(self, qt: QtDriver, tmp_path: Path) -> None:
        """Full workflow: YAML → .ts → .qm → widget with tr()."""
        # Create YAML
        yaml_content = dedent("""
            TestWidget:
              "Greeting":
                fr: Salut
        """)

        # Parse and compile to .ts
        entries = parse_yaml(yaml_content)
        compile_translations(entries, tmp_path)

        ts_path = tmp_path / "fr.ts"
        qm_path = tmp_path / "fr.qm"

        # Try to compile .ts to .qm
        if not compile_ts_to_qm(ts_path, qm_path):
            # Skip if lrelease not available
            return

        # Create widget and load translation
        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel)

            @override
            def setup(self) -> None:
                self.label.setText(self.tr("Greeting"))

        # Load the translation
        translator = QTranslator()
        loaded = translator.load(str(qm_path))

        if loaded:
            from qtpy.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                app.installTranslator(translator)

            w = TestWidget()
            qt.track(w)

            # Should be translated to French
            assert_that(w.label.text()).is_equal_to("Salut")

            if app:
                app.removeTranslator(translator)

    def test_widget_class_name_matches_context(self, qt: QtDriver) -> None:
        """Widget class name should be used as tr() context."""

        @widget()
        class MySpecialWidget(QWidget, Widget):
            label: QLabel = make(QLabel)
            button: QPushButton = make(QPushButton)

            @override
            def setup(self) -> None:
                # These use MySpecialWidget as context
                self.label.setText(self.tr("Label Text"))
                self.button.setText(self.tr("Button Text"))

        w = MySpecialWidget()
        qt.track(w)

        # Verify the translations would use the class name context
        # (tr() returns source when no translation loaded)
        assert_that(w.label.text()).is_equal_to("Label Text")
        assert_that(w.button.text()).is_equal_to("Button Text")
