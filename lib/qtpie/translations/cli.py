"""CLI for yaml-to-tr command."""

import argparse
import sys
from glob import glob
from pathlib import Path

from qtpie.translations.compiler import compile_translations
from qtpie.translations.parser import parse_yaml_files


def main(argv: list[str] | None = None) -> int:
    """Main entry point for yaml-to-tr CLI."""
    parser = argparse.ArgumentParser(
        prog="yaml-to-tr",
        description="Compile YAML translation files to Qt .ts format",
    )

    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input YAML files or glob patterns (e.g., 'translations/*.tr.yml')",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("."),
        help="Output directory for .ts files (default: current directory)",
    )

    parser.add_argument(
        "-p",
        "--prefix",
        default="",
        help="Prefix for output filenames (e.g., 'myapp_' produces 'myapp_fr.ts')",
    )

    parser.add_argument(
        "-l",
        "--languages",
        nargs="*",
        help="Only compile specific languages (default: all found)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )

    args = parser.parse_args(argv)

    # Expand glob patterns and collect all input files
    input_files: list[Path] = []
    for pattern in args.inputs:
        matches = glob(pattern, recursive=True)
        if matches:
            input_files.extend(Path(m) for m in matches)
        else:
            # Treat as literal path
            path = Path(pattern)
            if path.exists():
                input_files.append(path)
            else:
                print(f"Error: No files found matching '{pattern}'", file=sys.stderr)
                return 1

    if not input_files:
        print("Error: No input files found", file=sys.stderr)
        return 1

    # Remove duplicates and sort
    input_files = sorted(set(input_files))

    if args.verbose:
        print(f"Parsing {len(input_files)} file(s):")
        for f in input_files:
            print(f"  - {f}")

    # Parse and compile
    entries = parse_yaml_files(input_files)

    if not entries:
        print("Warning: No translation entries found", file=sys.stderr)
        return 0

    if args.verbose:
        print(f"Found {len(entries)} translation entries")

    output_files = compile_translations(
        entries,
        args.output,
        languages=args.languages,
        prefix=args.prefix,
    )

    if args.verbose:
        print(f"Generated {len(output_files)} .ts file(s):")
        for f in output_files:
            print(f"  - {f}")
    else:
        for f in output_files:
            print(f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
