"""Main CLI entry point for qtpie commands."""

import typer

from qtpie.cli.tr import tr_app

app = typer.Typer(
    name="qtpie",
    help="QtPie CLI - Tools for QtPie applications",
    no_args_is_help=True,
)

# Add subcommands
app.add_typer(tr_app, name="tr", help="Translation commands")


def main() -> None:
    """Run the qtpie CLI."""
    app()


if __name__ == "__main__":
    main()
