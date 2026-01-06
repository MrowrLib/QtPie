"""SCSS to QSS compiler."""

from pathlib import Path
from typing import cast

from scss import Compiler  # type: ignore[import-untyped]


def compile_scss(
    scss_path: str,
    qss_path: str,
    search_paths: list[str] | None = None,
) -> None:
    """
    Compile SCSS file to QSS.

    Args:
        scss_path: Path to the main SCSS file.
        qss_path: Path where the compiled QSS will be written.
        search_paths: Directories to search for @import resolution.

    Raises:
        FileNotFoundError: If scss_path doesn't exist.
        scss.errors.SassError: If SCSS has syntax errors.
    """
    scss_file = Path(scss_path)
    qss_file = Path(qss_path)

    if not scss_file.exists():
        raise FileNotFoundError(f"SCSS file not found: {scss_path}")

    # Prepare search paths for @import resolution
    paths = [str(scss_file.parent)]
    if search_paths:
        paths.extend(search_paths)

    # Compile SCSS to CSS (QSS is a subset of CSS)
    compiler = Compiler(search_path=paths)
    qss_content = cast(str, compiler.compile(str(scss_file)))  # pyright: ignore[reportUnknownMemberType]

    # Ensure output directory exists
    qss_file.parent.mkdir(parents=True, exist_ok=True)

    # Write compiled QSS
    qss_file.write_text(qss_content)
