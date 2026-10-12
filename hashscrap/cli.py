"""Command-line entry point for HashScrap."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from hashscrap import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the initial CLI."""
    parser = argparse.ArgumentParser(
        prog="hashscrap",
        description="HashScrap — bounded collection and extraction for authorized public-source research.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="show the installed version and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI. With no arguments, display help and exit successfully."""
    parser = build_parser()
    if argv is not None and len(argv) == 0:
        parser.print_help()
        return 0
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
