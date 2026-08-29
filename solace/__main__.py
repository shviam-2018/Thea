"""Minimal Solace command-line entry point."""

from __future__ import annotations

import argparse
import sys

from . import display_version
from .commands import handle_slash_command
from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Solace local application utilities")
    parser.add_argument(
        "command",
        nargs="?",
        default="/status",
        help="slash command (default: /status)",
    )
    parser.add_argument("--config", help="path to a Solace JSON configuration file")
    parser.add_argument("--version", action="version", version=f"Solace {display_version()}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        command = args.command if args.command.startswith("/") else f"/{args.command}"
        output = handle_slash_command(command, config)
    except (OSError, TypeError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    if output is None:
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
