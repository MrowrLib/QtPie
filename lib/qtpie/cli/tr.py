"""Translation CLI commands."""
# ruff: noqa: B008  # Typer uses function calls in defaults by design

from pathlib import Path

import typer

tr_app = typer.Typer(help="Translation management commands")


@tr_app.command("compile")
def compile_command(
    input_files: list[Path] = typer.Argument(
        ...,
        help="YAML translation file(s) to compile",
        exists=True,
    ),
    output: Path = typer.Option(
        Path("./i18n"),
        "-o",
        "--output",
        help="Output directory for compiled files",
    ),
    qm: bool = typer.Option(
        False,
        "--qm",
        help="Also compile to Qt .qm binary format (requires lrelease)",
    ),
    lang: list[str] | None = typer.Option(
        None,
        "--lang",
        "-l",
        help="Languages to compile (default: all found in YAML)",
    ),
) -> None:
    """Compile YAML translations to Qt .ts and optionally .qm files.

    Examples:
        # Compile all languages to .ts files
        qtpie tr compile app.yml -o ./i18n/

        # Also generate .qm binary files
        qtpie tr compile app.yml -o ./i18n/ --qm

        # Only compile specific languages
        qtpie tr compile app.yml -o ./i18n/ --lang fr --lang de
    """
    from qtpie.translations import (
        compile_all_qm,
        compile_translations,
        get_all_languages,
        parse_yaml_files,
    )

    # Parse input files
    typer.echo(f"Parsing {len(input_files)} translation file(s)...")
    entries = parse_yaml_files([str(p) for p in input_files])

    if not entries:
        typer.echo("No translations found in input files.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Found {len(entries)} translation entries.")

    # Determine languages to compile
    if lang:
        languages = list(lang)
    else:
        languages = list(get_all_languages(entries))

    if not languages:
        typer.echo("No languages found to compile.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Compiling languages: {', '.join(languages)}")

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)

    # Compile to .ts files
    ts_files = compile_translations(entries, output, languages=languages)
    typer.echo(f"Generated {len(ts_files)} .ts file(s) in {output}/")

    # Optionally compile to .qm
    if qm:
        typer.echo("Compiling to .qm binary format...")
        try:
            qm_files = compile_all_qm(ts_files)
            typer.echo(f"Generated {len(qm_files)} .qm file(s)")
        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e

    typer.echo("Done!")


@tr_app.command("list")
def list_command(
    input_files: list[Path] = typer.Argument(
        ...,
        help="YAML translation file(s) to inspect",
        exists=True,
    ),
) -> None:
    """List all translations and their available languages.

    Examples:
        qtpie tr list app.yml
    """
    from qtpie.translations import get_all_languages, parse_yaml_files

    entries = parse_yaml_files([str(p) for p in input_files])

    if not entries:
        typer.echo("No translations found.")
        return

    languages = get_all_languages(entries)
    typer.echo(f"Languages: {', '.join(languages) if languages else 'none'}")
    typer.echo(f"Entries: {len(entries)}")
    typer.echo("")

    # Group by context
    by_context: dict[str, list[tuple[str, str | None]]] = {}
    for entry in entries:
        ctx = entry.context if entry.context != "@default" else "(global)"
        if ctx not in by_context:
            by_context[ctx] = []
        by_context[ctx].append((entry.source, entry.disambiguation))

    for ctx, items in sorted(by_context.items()):
        typer.echo(f"[{ctx}]")
        for source, disambig in items:
            if disambig:
                typer.echo(f"  {source} | {disambig}")
            else:
                typer.echo(f"  {source}")
        typer.echo("")
