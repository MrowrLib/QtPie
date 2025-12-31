"""Tests for stylesheet loader."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from qtpie.styles import load_stylesheet


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
    def mock_qfile(self) -> tuple[MagicMock, MagicMock]:
        """Create a mock QFile that returns fake QRC content."""
        mock_file = MagicMock()
        mock_file.open.return_value = True

        mock_stream = MagicMock()
        mock_stream.readAll.return_value = "QPushButton { background-color: red; }"

        return mock_file, mock_stream

    def test_loads_from_qrc(self, mock_qfile: tuple[MagicMock, MagicMock]) -> None:
        """Loads content from QRC resource."""
        mock_file, mock_stream = mock_qfile

        with (
            patch("qtpie.styles.loader.QFile", return_value=mock_file),
            patch("qtpie.styles.loader.QTextStream", return_value=mock_stream),
        ):
            result = load_stylesheet(qrc_path=":/styles/test_styles.qss")

        assert_that(result).contains("QPushButton")
        assert_that(result).contains("background-color: red")

    def test_returns_empty_for_missing_qrc(self) -> None:
        """Returns empty string if QRC path doesn't exist."""
        mock_file = MagicMock()
        mock_file.open.return_value = False  # File doesn't exist

        with patch("qtpie.styles.loader.QFile", return_value=mock_file):
            result = load_stylesheet(qrc_path=":/nonexistent/styles.qss")

        assert_that(result).is_equal_to("")


class TestLoadStylesheetFallback:
    """Tests for local-to-QRC fallback behavior."""

    def test_local_takes_precedence_over_qrc(self, tmp_path: Path) -> None:
        """Local file is used when both local and QRC are provided."""
        local_qss = tmp_path / "local.qss"
        local_qss.write_text("QLabel { color: blue; }")

        # QRC should never be touched since local exists
        result = load_stylesheet(
            qss_path=str(local_qss),
            qrc_path=":/styles/test_styles.qss",
        )

        # Should get local content, not QRC
        assert_that(result).contains("QLabel")
        assert_that(result).contains("color: blue")

    def test_falls_back_to_qrc_when_local_missing(self) -> None:
        """Falls back to QRC when local file doesn't exist."""
        mock_file = MagicMock()
        mock_file.open.return_value = True

        mock_stream = MagicMock()
        mock_stream.readAll.return_value = "QPushButton { background-color: red; }"

        with (
            patch("qtpie.styles.loader.QFile", return_value=mock_file),
            patch("qtpie.styles.loader.QTextStream", return_value=mock_stream),
        ):
            result = load_stylesheet(
                qss_path="/nonexistent/styles.qss",
                qrc_path=":/styles/test_styles.qss",
            )

        # Should get QRC content
        assert_that(result).contains("QPushButton")
        assert_that(result).contains("background-color: red")
