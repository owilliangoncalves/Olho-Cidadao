"""Helpers puros usados pelas orquestrações do pacote `pipeline`."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable
from typing import Iterable

from infra.errors import UserInputError


@dataclass(frozen=True)
class TarefaParalela:
    """Representa uma unidade independente de execução do pipeline paralelo."""

    nome: str
    executar: Callable[[], None]


def validar_intervalo_anos(
    ano_inicio: int | None,
    ano_fim: int | None,
    *,
    contexto: str,
    required: bool,
) -> None:
    """Valida um intervalo anual exclusivo."""

    if required and (ano_inicio is None or ano_fim is None):
        raise UserInputError(
            f"O pipeline {contexto} exige ano_inicio e ano_fim. "
            "Defina a configuração correspondente no etl-config.toml "
            "ou informe --ano-inicio/--ano-fim."
        )

    if ano_inicio is not None and ano_fim is not None and ano_inicio >= ano_fim:
        raise UserInputError(
            f"ano_inicio deve ser menor que ano_fim no pipeline {contexto}."
        )


def validar_intervalo_datas(
    data_inicial,
    data_final,
    *,
    contexto: str,
    campo_inicial: str,
    campo_final: str,
) -> None:
    """Valida uma janela temporal não vazia e ordenada."""

    if data_inicial is None or data_final is None:
        raise UserInputError(
            f"O pipeline {contexto} exige {campo_inicial} e {campo_final}. "
            "Defina a configuração correspondente no etl-config.toml "
            f"ou informe --{campo_inicial.replace('_', '-')}/--{campo_final.replace('_', '-')}."
        )

    if data_inicial > data_final:
        raise UserInputError(
            f"{campo_inicial} nao pode ser maior que {campo_final}."
        )


def validar_max_workers(max_workers: int | None, *, contexto: str) -> None:
    """Valida o paralelismo máximo configurado para um pipeline."""

    if max_workers is None:
        raise UserInputError(
            f"O pipeline {contexto} exige max_workers. "
            "Defina a configuração correspondente no etl-config.toml "
            "ou informe --max-workers."
        )

    if max_workers < 1:
        raise UserInputError("max_workers deve ser maior ou igual a 1.")


def portal_api_key_configurada() -> bool:
    """Indica se o ambiente possui chave para a API do Portal."""

    return bool(
        os.getenv("PORTAL_TRANSPARENCIA_API_KEY")
        or os.getenv("CHAVE_API_DADOS")
    )


def documentos_fornecedores(fornecedores: Iterable[dict]) -> list[str]:
    """Extrai os documentos disponíveis da dimensão local de fornecedores."""

    return [
        item["documento"]
        for item in fornecedores
        if item.get("documento")
    ]
