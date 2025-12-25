"""Translation CLI commands."""

from pathlib import Path
from typing import Annotated

import typer

from qtpie.translations.compiler import (
    compile_all_qm,
    compile_translations,
    get_all_languages,
)
from qtpie.translations.parser import parse_yaml_files

app = typer.Typer(
    name="tr",
    help="Translation tools for compiling YAML to .ts and .qm files.",
    no_args_is_help=True,
)


@app.command()
def compile(
    files: Annotated[
        list[Path],
        typer.Argument(
            help="YAML translation file(s) to compile.",
            exists=True,
            dir_okay=False,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output directory for .ts (and .qm) files.",
        ),
    ],
    qm: Annotated[
        bool,
        typer.Option(
            "--qm",
            help="Also compile .ts to .qm binary files.",
        ),
    ] = False,
    languages: Annotated[
        list[str] | None,
        typer.Option(
            "--lang",
            "-l",
            help="Only compile specific language(s). Can be repeated.",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed output.",
        ),
    ] = False,
) -> None:
    """Compile YAML translations to .ts (and optionally .qm) files.

    Examples:

        qtpie tr compile app.yml -o ./i18n/

        qtpie tr compile app.yml -o ./i18n/ --qm

        qtpie tr compile app.yml -o ./i18n/ --lang fr --lang de
    """
    # Parse YAML files
    if verbose:
        typer.echo(f"Parsing {len(files)} YAML file(s)...")

    entries = parse_yaml_files(files)

    if not entries:
        typer.echo("No translation entries found.", err=True)
        raise typer.Exit(1)

    # Show available languages
    all_langs = get_all_languages(entries)
    if verbose:
        typer.echo(f"Found languages: {', '.join(sorted(all_langs))}")

    # Filter languages if specified
    target_langs = list(languages) if languages else None
    if target_langs:
        missing = set(target_langs) - all_langs
        if missing:
            typer.echo(f"Warning: Languages not found in YAML: {', '.join(missing)}", err=True)

    # Compile to .ts
    if verbose:
        typer.echo(f"Compiling to {output}/...")

    ts_files = compile_translations(
        entries,
        output,
        languages=target_langs,
    )

    for ts_file in ts_files:
        typer.echo(f"  {ts_file}")

    # Compile to .qm if requested
    if qm:
        if verbose:
            typer.echo("Compiling .ts to .qm...")

        try:
            qm_files = compile_all_qm(ts_files)
            for qm_file in qm_files:
                typer.echo(f"  {qm_file}")
        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            typer.echo("Hint: Install PySide6 (includes pyside6-lrelease) or Qt tools.", err=True)
            raise typer.Exit(1) from None
        except RuntimeError as e:
            typer.echo(f"Error compiling .qm: {e}", err=True)
            raise typer.Exit(1) from None

    # Summary
    if qm:
        typer.echo(f"Created {len(ts_files)} .ts and {len(ts_files)} .qm files.")
    else:
        typer.echo(f"Created {len(ts_files)} .ts files.")
