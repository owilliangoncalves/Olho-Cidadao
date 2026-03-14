"""Interface pública da camada de CLI do projeto."""

from .app import build_parser
from .app import main
from .app import parse_data_iso
from .app import run_command

__all__ = ["build_parser", "main", "parse_data_iso", "run_command"]
