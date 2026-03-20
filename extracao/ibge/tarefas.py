"""Helpers puros para o extrator de localidades do IBGE."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from extracao.ibge.config import IBGE_DATASETS


def output_path_localidade(dataset: str) -> Path:
    """Retorna o caminho relativo de saída de um dataset do IBGE."""

    return Path("ibge") / "localidades" / f"{dataset}.json"


def resolver_datasets_solicitados(
    datasets: Iterable[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Separa datasets válidos e inválidos preservando a ordem de entrada."""

    if datasets is None:
        return tuple(IBGE_DATASETS), ()

    validos: list[str] = []
    invalidos: list[str] = []
    vistos_validos: set[str] = set()
    vistos_invalidos: set[str] = set()
    for dataset in datasets:
        if dataset in IBGE_DATASETS:
            if dataset in vistos_validos:
                continue
            vistos_validos.add(dataset)
            validos.append(dataset)
        else:
            if dataset in vistos_invalidos:
                continue
            vistos_invalidos.add(dataset)
            invalidos.append(dataset)

    return tuple(validos), tuple(invalidos)
