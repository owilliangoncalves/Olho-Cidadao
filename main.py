"""Ponto de entrada enxuto da CLI do projeto."""

from cli.app import build_parser
from cli.app import main
from cli.app import parse_data_iso
from cli.app import run_command

__all__ = ["build_parser", "main", "parse_data_iso", "run_command"]


if __name__ == "__main__":
    main()
