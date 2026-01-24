"""SCSS to QSS compiler."""

from pathlib import Path
from typing import cast

from scss import Compiler  # type: ignore[import-untyped]


def compile_scss(
    scss_path: str,
    qss_path: str,
    search_paths: list[str] | None = None,
    variables: dict[str, str] | None = None,
    use_global_variables: bool = True,
) -> None:
    """
    Compile SCSS file to QSS.

    Args:
        scss_path: Path to the main SCSS file.
        qss_path: Path where the compiled QSS will be written.
        search_paths: Directories to search for @import resolution.
        variables: Optional dictionary of SCSS variables to inject.
            Keys are variable names (without $), values are SCSS expressions.
        use_global_variables: If True, also include global variables from
            the zoom module. Local variables override global ones.

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

    # Build variable injection
    all_variables: dict[str, str] = {}

    # Global variables from zoom module (if enabled)
    if use_global_variables:
        from qtpie.styles.zoom import get_scss_variables

        all_variables.update(get_scss_variables())

    # Local variables override global
    if variables:
        all_variables.update(variables)

    # Build the SCSS content with injected variables
    scss_content = scss_file.read_text()

    if all_variables:
        variable_lines = ["// Injected variables from Python"]
        for name, value in all_variables.items():
            # Use !default so SCSS file can override if needed
            variable_lines.append(f"${name}: {value} !default;")
        variable_lines.append("")  # Blank line
        variable_prefix = "\n".join(variable_lines)
        scss_content = variable_prefix + scss_content

    # Compile SCSS to CSS (QSS is a subset of CSS)
    compiler = Compiler(search_path=paths)
    qss_content = cast(str, compiler.compile_string(scss_content))  # pyright: ignore[reportUnknownMemberType]

    # Ensure output directory exists
    qss_file.parent.mkdir(parents=True, exist_ok=True)

    # Write compiled QSS
    qss_file.write_text(qss_content)
