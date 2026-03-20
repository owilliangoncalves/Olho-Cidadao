"""Helpers puros para tarefas do extrator de revendedores da ANP."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

STATUS_TO_COUNTER = {
    "success": "completed",
    "skipped": "skipped",
    "skipped_empty": "skipped",
}


def output_path_revendedor(dataset: str, documento: str) -> Path:
    """Monta o caminho de saída de uma consulta por CNPJ."""

    return Path("anp") / "revendedores" / dataset / f"fornecedor={documento}.json"


def iterar_tarefas_revendedores(
    datasets: Iterable[str],
    documentos: Iterable[str],
) -> Iterator[tuple[str, str]]:
    """Expande datasets e documentos em tarefas `(dataset, documento)`."""

    for dataset in datasets:
        for documento in documentos:
            yield dataset, documento


def contador_por_status(status: str | None) -> str:
    """Mapeia o status da base pública para o contador do crawler."""

    return STATUS_TO_COUNTER.get(status, "empty")
