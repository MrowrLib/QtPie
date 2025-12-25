"""Main qtpie CLI entry point."""

import typer

from qtpie.cli.tr import app as tr_app

app = typer.Typer(
    name="qtpie",
    help="QtPie CLI - tools for building Qt apps.",
    no_args_is_help=True,
)

app.add_typer(tr_app, name="tr", help="Translation tools.")


def main() -> None:
    """Entry point for the qtpie CLI."""
    app()


if __name__ == "__main__":
    main()
