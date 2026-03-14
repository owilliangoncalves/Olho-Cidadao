"""Orquestra a execução da CLI do projeto."""

from __future__ import annotations

import argparse
import sys

from configuracao.logger import logger
from infra.errors import UserInputError

from .common import parse_data_iso
from .handlers import HANDLERS
from .parser import build_parser


def run_command(args: argparse.Namespace):
    """Despacha o comando selecionado para o handler correspondente."""

    HANDLERS[args.comando](args)


def main(argv: list[str] | None = None):
    """Inicializa a CLI, interpreta argumentos e executa o comando selecionado."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        run_command(args)
    except UserInputError as exc:
        logger.error("%s", exc)
        sys.exit(2)
    except Exception:
        logger.exception("A execução falhou:")
        sys.exit(1)


__all__ = ["build_parser", "main", "parse_data_iso", "run_command"]
