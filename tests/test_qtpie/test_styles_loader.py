"""Tests for stylesheet loader."""

import shutil
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from assertpy import assert_that

from qtpie.styles import load_stylesheet

FIXTURES = Path(__file__).parent / "fixtures"


def _compile_qrc(qrc_path: Path, output_path: Path) -> None:
    """Compile QRC file to Python module using pyside6-rcc."""
    rcc_exe = shutil.which("pyside6-rcc")
    if rcc_exe is None:
        pytest.skip("pyside6-rcc not found")

    subprocess.run(
        [rcc_exe, str(qrc_path), "-o", str(output_path)],
        check=True,
        cwd=str(qrc_path.parent),  # So relative paths in .qrc work
    )


class TestLoadStylesheetLocal:
    """Tests for loading from local QSS files."""

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        """Loads content from existing local QSS file."""
        qss_file = tmp_path / "styles.qss"
        qss_file.write_text("QPushButton { color: red; }")

        result = load_stylesheet(qss_path=str(qss_file))

        assert_that(result).contains("QPushButton")
        assert_that(result).contains("color: red")

    def test_returns_empty_for_missing_file(self) -> None:
        """Returns empty string if local file doesn't exist."""
        result = load_stylesheet(qss_path="/nonexistent/path/styles.qss")

        assert_that(result).is_equal_to("")

    def test_returns_empty_when_no_paths_provided(self) -> None:
        """Returns empty string if no paths provided."""
        result = load_stylesheet()

        assert_that(result).is_equal_to("")


class TestLoadStylesheetQrc:
    """Tests for loading from QRC resources."""

    @pytest.fixture
    def compiled_qrc(self, tmp_path: Path) -> Generator[None]:
        """Compile QRC and register resources for test."""
        qrc_path = FIXTURES / "qrc" / "resources.qrc"
        output_path = tmp_path / "resources_rc.py"

        _compile_qrc(qrc_path, output_path)

        # Import to register resources
        sys.path.insert(0, str(tmp_path))
        import resources_rc  # type: ignore[import-not-found] # noqa: F401

        yield

        # Cleanup
        sys.path.remove(str(tmp_path))
        # Remove from sys.modules so it can be reimported in other tests
        if "resources_rc" in sys.modules:
            del sys.modules["resources_rc"]

    def test_loads_from_qrc(self, compiled_qrc: None) -> None:
        """Loads content from QRC resource."""
        result = load_stylesheet(qrc_path=":/styles/test_styles.qss")

        assert_that(result).contains("QPushButton")
        assert_that(result).contains("background-color: red")

    def test_returns_empty_for_missing_qrc(self) -> None:
        """Returns empty string if QRC path doesn't exist."""
        result = load_stylesheet(qrc_path=":/nonexistent/styles.qss")

        assert_that(result).is_equal_to("")


class TestLoadStylesheetFallback:
    """Tests for local-to-QRC fallback behavior."""

    @pytest.fixture
    def compiled_qrc(self, tmp_path: Path) -> Generator[None]:
        """Compile QRC and register resources for test."""
        qrc_path = FIXTURES / "qrc" / "resources.qrc"
        output_path = tmp_path / "resources_rc.py"

        _compile_qrc(qrc_path, output_path)

        sys.path.insert(0, str(tmp_path))
        import resources_rc  # type: ignore[import-not-found] # noqa: F401

        yield

        sys.path.remove(str(tmp_path))
        if "resources_rc" in sys.modules:
            del sys.modules["resources_rc"]

    def test_local_takes_precedence_over_qrc(self, tmp_path: Path, compiled_qrc: None) -> None:
        """Local file is used when both local and QRC are provided."""
        local_qss = tmp_path / "local.qss"
        local_qss.write_text("QLabel { color: blue; }")

        result = load_stylesheet(
            qss_path=str(local_qss),
            qrc_path=":/styles/test_styles.qss",
        )

        # Should get local content, not QRC
        assert_that(result).contains("QLabel")
        assert_that(result).contains("color: blue")
        assert_that(result).does_not_contain("background-color: red")

    def test_falls_back_to_qrc_when_local_missing(self, compiled_qrc: None) -> None:
        """Falls back to QRC when local file doesn't exist."""
        result = load_stylesheet(
            qss_path="/nonexistent/styles.qss",
            qrc_path=":/styles/test_styles.qss",
        )

        # Should get QRC content
        assert_that(result).contains("QPushButton")
        assert_that(result).contains("background-color: red")
