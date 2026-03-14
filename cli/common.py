"""Helpers compartilhados pela CLI."""

from __future__ import annotations

import argparse
from datetime import date
from datetime import datetime

from configuracao.projeto import obter_intervalo_anos_padrao


def parse_data_iso(valor: str) -> date:
    """Converte uma data ISO (`YYYY-MM-DD`) para `date`."""

    return datetime.strptime(valor, "%Y-%m-%d").date()


def adicionar_args_intervalo_anos(
    parser: argparse.ArgumentParser,
    *,
    usar_defaults_compartilhados: bool = True,
):
    """Adiciona argumentos padronizados de intervalo anual à CLI."""

    defaults = obter_intervalo_anos_padrao() if usar_defaults_compartilhados else {}
    help_ano_inicio = None
    help_ano_fim = "Ano final exclusivo. Ex.: 2026 processa ate 2025."
    if not usar_defaults_compartilhados:
        help_ano_inicio = (
            "Se omitido, usa a configuracao especifica do pipeline no etl-config.toml."
        )
        help_ano_fim = (
            "Ano final exclusivo. Se omitido, usa a configuracao especifica "
            "do pipeline no etl-config.toml."
        )

    parser.add_argument(
        "--ano-inicio",
        type=int,
        default=defaults.get("ano_inicio"),
        help=help_ano_inicio,
    )
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=defaults.get("ano_fim"),
        help=help_ano_fim,
    )


def adicionar_flag_inclusao(
    parser: argparse.ArgumentParser,
    *,
    nome: str,
    destino: str,
    descricao: str,
):
    """Adiciona uma flag booleana tri-state controlada pela CLI.

    Quando nenhuma flag e passada, o valor permanece ``None`` e a decisao fica
    a cargo do ``etl-config.toml``. Quando a CLI informa ``--<nome>`` ou
    ``--sem-<nome>``, esse override tem prioridade apenas para a execucao atual.
    """

    parser.add_argument(
        f"--{nome}",
        dest=destino,
        action="store_true",
        default=None,
        help=(
            f"Forca {descricao} nesta execucao, sobrescrevendo "
            "o etl-config.toml."
        ),
    )
    parser.add_argument(
        f"--sem-{nome}",
        dest=destino,
        action="store_false",
        help=(
            f"Desabilita {descricao} nesta execucao, sobrescrevendo "
            "o etl-config.toml."
        ),
    )
