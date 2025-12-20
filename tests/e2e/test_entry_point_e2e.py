"""End-to-end tests for @entry_point using subprocess.

These tests actually run Python scripts in subprocesses to test
the full @entry_point behavior including auto-run.

These tests are marked with @pytest.mark.e2e and can be skipped with:
    pytest -m "not e2e"
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from assertpy import assert_that

# Get the project root so we can set PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_script(script_path: Path, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    """Run a Python script with qtpie on the path."""
    env = os.environ.copy()
    # Set PYTHONPATH to include the project root (so `import qtpie` works)
    project_path = str(PROJECT_ROOT)
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_path}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = project_path

    # Clear Qt-related env vars to prevent inheriting parent Qt state (macOS fork issue)
    for key in list(env.keys()):
        if key.startswith(("QT_", "DISPLAY", "XDG_")):
            del env[key]

    return subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        start_new_session=True,  # Isolate from parent Qt process on macOS
    )


@pytest.mark.e2e
class TestEntryPointFunctionE2E:
    """E2E tests for @entry_point on functions."""

    def test_entry_point_function_runs(self, tmp_path: Path) -> None:
        """@entry_point on a function should run when executed directly."""
        script = tmp_path / "app.py"
        script.write_text("""
from qtpie import entry_point
from qtpy.QtWidgets import QLabel, QApplication
from qtpy.QtCore import QTimer

@entry_point
def main():
    print("MAIN_CALLED")
    label = QLabel("Test")
    print(f"LABEL_TEXT={label.text()}")
    # Exit immediately after event loop starts
    QTimer.singleShot(0, QApplication.quit)
    return label
""")
        result = run_script(script)
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("MAIN_CALLED")
        assert_that(result.stdout).contains("LABEL_TEXT=Test")

    def test_entry_point_function_with_config(self, tmp_path: Path) -> None:
        """@entry_point with config should apply settings."""
        script = tmp_path / "app.py"
        script.write_text("""
from qtpie import entry_point
from qtpy.QtWidgets import QLabel, QApplication
from qtpy.QtCore import QTimer

@entry_point(title="My Test App", size=(800, 600))
def main():
    label = QLabel("Configured")
    print(f"TITLE={label.windowTitle()}")  # Will be empty until shown
    # Exit immediately
    QTimer.singleShot(0, QApplication.quit)
    return label
""")
        result = run_script(script)
        assert_that(result.returncode).is_equal_to(0)


@pytest.mark.e2e
class TestEntryPointWidgetClassE2E:
    """E2E tests for @entry_point on widget classes."""

    def test_entry_point_widget_class_runs(self, tmp_path: Path) -> None:
        """@entry_point on a @widget class should run when executed."""
        script = tmp_path / "app.py"
        script.write_text("""
from qtpie import entry_point, widget, make
from qtpy.QtWidgets import QWidget, QLabel, QApplication
from qtpy.QtCore import QTimer

@entry_point
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Hello from widget!")

    def setup(self):
        print("SETUP_CALLED")
        print(f"LABEL={self.label.text()}")
        QTimer.singleShot(0, QApplication.quit)
""")
        result = run_script(script)
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("SETUP_CALLED")
        assert_that(result.stdout).contains("LABEL=Hello from widget!")


@pytest.mark.e2e
class TestEntryPointImportBehavior:
    """Tests for @entry_point import behavior."""

    def test_import_does_not_autorun(self, tmp_path: Path) -> None:
        """
        When a module with @entry_point is IMPORTED (not run directly),
        the app should NOT auto-run.
        """
        # App module with @entry_point
        app_script = tmp_path / "myapp.py"
        app_script.write_text("""
from qtpie import entry_point, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@entry_point
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Test")

    def setup(self):
        print("APP_STARTED")  # Should NOT appear when imported
""")

        # Another script that imports myapp
        import_script = tmp_path / "importer.py"
        import_script.write_text(f'''
import sys
sys.path.insert(0, "{tmp_path}")

# This imports myapp, but myapp.__module__ == "myapp", not "__main__"
# So @entry_point should NOT auto-run
from myapp import MyApp

print("IMPORT_SUCCESS")
print(f"CLASS={{MyApp.__name__}}")
''')

        result = run_script(import_script)
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("IMPORT_SUCCESS")
        assert_that(result.stdout).contains("CLASS=MyApp")
        # App should NOT have started
        assert_that(result.stdout).does_not_contain("APP_STARTED")


@pytest.mark.e2e
class TestEntryPointAppSubclass:
    """E2E tests for @entry_point on App subclasses."""

    def test_entry_point_app_subclass_runs(self, tmp_path: Path) -> None:
        """@entry_point on an App subclass should use that App."""
        script = tmp_path / "app.py"
        script.write_text("""
from qtpie import App, entry_point
from qtpy.QtWidgets import QLabel, QApplication
from qtpy.QtCore import QTimer

@entry_point
class MyApp(App):
    def setup(self):
        print("APP_SETUP_CALLED")
        print(f"APP_NAME={self.applicationName()}")

    def create_window(self):
        print("CREATE_WINDOW_CALLED")
        label = QLabel("From App subclass")
        QTimer.singleShot(0, QApplication.quit)
        return label
""")
        result = run_script(script)
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("APP_SETUP_CALLED")
        assert_that(result.stdout).contains("CREATE_WINDOW_CALLED")


@pytest.mark.e2e
class TestRunAppFunction:
    """E2E tests for the run_app standalone function."""

    def test_run_app_with_plain_qapplication(self, tmp_path: Path) -> None:
        """run_app should work with a plain QApplication."""
        script = tmp_path / "app.py"
        script.write_text("""
from qtpy.QtWidgets import QApplication, QLabel
from qtpy.QtCore import QTimer
from qtpie import run_app

app = QApplication([])
print("APP_CREATED")

label = QLabel("Hello run_app")
label.show()
print(f"LABEL={label.text()}")

QTimer.singleShot(0, app.quit)
run_app(app)
print("APP_FINISHED")
""")
        result = run_script(script)
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("APP_CREATED")
        assert_that(result.stdout).contains("LABEL=Hello run_app")
        assert_that(result.stdout).contains("APP_FINISHED")
