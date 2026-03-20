"""Helpers puros para o pacote do ObrasGov."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from extracao.obrasgov.config import PAGEABLE_RESOURCES
from extracao.obrasgov.projetos import slug_id

STATUS_TO_COUNTER = {
    "success": "completed",
    "skipped": "skipped",
    "skipped_empty": "skipped",
}


def contador_por_status(status: str | None) -> str:
    """Mapeia o status da base pública para o contador do crawler."""

    return STATUS_TO_COUNTER.get(status, "empty")


def output_path_recurso(recurso: str, assinatura: str) -> Path:
    """Retorna o caminho relativo de saída de um recurso paginado."""

    return Path("obrasgov") / recurso / f"consulta={assinatura}.json"


def output_path_geometria(id_unico: str) -> Path:
    """Retorna o caminho relativo de saída de uma geometria."""

    return Path("obrasgov") / "geometria" / f"projeto={slug_id(id_unico)}.json"


def resolver_recursos_paginados(
    recursos: Iterable[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Separa recursos válidos e inválidos preservando a ordem de entrada."""

    if recursos is None:
        return tuple(PAGEABLE_RESOURCES), ()

    validos: list[str] = []
    invalidos: list[str] = []
    vistos_validos: set[str] = set()
    vistos_invalidos: set[str] = set()
    for recurso in recursos:
        if recurso in PAGEABLE_RESOURCES:
            if recurso in vistos_validos:
                continue
            vistos_validos.add(recurso)
            validos.append(recurso)
        else:
            if recurso in vistos_invalidos:
                continue
            vistos_invalidos.add(recurso)
            invalidos.append(recurso)

    return tuple(validos), tuple(invalidos)
