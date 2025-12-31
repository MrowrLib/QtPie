"""Tests for SCSS to QSS compiler."""

from pathlib import Path

import pytest
from assertpy import assert_that

from qtpie.styles import compile_scss

FIXTURES = Path(__file__).parent / "fixtures" / "scss"


class TestCompileScss:
    """Tests for compile_scss function."""

    def test_single_file_compiles(self, tmp_path: Path) -> None:
        """Simple SCSS file compiles to QSS."""
        qss_path = tmp_path / "output.qss"

        compile_scss(
            scss_path=str(FIXTURES / "single_file" / "simple.scss"),
            qss_path=str(qss_path),
        )

        assert_that(qss_path.exists()).is_true()
        qss = qss_path.read_text()
        assert_that(qss).contains("QPushButton")
        assert_that(qss).contains("background-color: blue")

    def test_one_search_dir_resolves_imports(self, tmp_path: Path) -> None:
        """SCSS with @import resolves from search path."""
        qss_path = tmp_path / "output.qss"

        compile_scss(
            scss_path=str(FIXTURES / "one_search_dir" / "main.scss"),
            qss_path=str(qss_path),
            search_paths=[str(FIXTURES / "one_search_dir" / "partials")],
        )

        assert_that(qss_path.exists()).is_true()
        qss = qss_path.read_text()
        # Variable $primary: #007bff should be resolved
        assert_that(qss).contains("#007bff")
        assert_that(qss).contains("QPushButton")

    def test_two_search_dirs_resolves_imports(self, tmp_path: Path) -> None:
        """SCSS with @import resolves from multiple search paths."""
        qss_path = tmp_path / "output.qss"

        compile_scss(
            scss_path=str(FIXTURES / "two_search_dirs" / "main.scss"),
            qss_path=str(qss_path),
            search_paths=[
                str(FIXTURES / "two_search_dirs" / "core"),
                str(FIXTURES / "two_search_dirs" / "themes"),
            ],
        )

        assert_that(qss_path.exists()).is_true()
        qss = qss_path.read_text()
        # Variables from core/_variables.scss should be resolved in themes/_theme.scss
        assert_that(qss).contains("16px")  # $base-size
        assert_that(qss).contains("#333333")  # $base-color
        assert_that(qss).contains("#ff6600")  # $accent-color

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Output directory is created if it doesn't exist."""
        qss_path = tmp_path / "nested" / "deep" / "output.qss"

        compile_scss(
            scss_path=str(FIXTURES / "single_file" / "simple.scss"),
            qss_path=str(qss_path),
        )

        assert_that(qss_path.exists()).is_true()

    def test_raises_on_missing_scss_file(self, tmp_path: Path) -> None:
        """FileNotFoundError raised if SCSS file doesn't exist."""
        qss_path = tmp_path / "output.qss"

        with pytest.raises(FileNotFoundError, match="SCSS file not found"):
            compile_scss(
                scss_path=str(tmp_path / "nonexistent.scss"),
                qss_path=str(qss_path),
            )

    def test_raises_on_scss_syntax_error(self, tmp_path: Path) -> None:
        """Error raised if SCSS has syntax errors."""
        from scss.errors import SassError  # type: ignore[import-untyped]

        bad_scss = tmp_path / "bad.scss"
        bad_scss.write_text("QPushButton { color: $undefined_variable; }")
        qss_path = tmp_path / "output.qss"

        with pytest.raises(SassError):
            compile_scss(
                scss_path=str(bad_scss),
                qss_path=str(qss_path),
            )
