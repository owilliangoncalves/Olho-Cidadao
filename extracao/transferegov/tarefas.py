"""Helpers puros para o pacote Transferegov."""

from __future__ import annotations

from pathlib import Path

from extracao.transferegov.config import RESOURCE_GROUPS
from extracao.transferegov.config import validar_grupo_transferegov
from utils.filtros import slug_filtros


def resolver_recursos_grupo(
    grupo: str,
    recursos: list[str] | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Separa recursos válidos e inválidos preservando ordem e sem repetir."""

    grupo = validar_grupo_transferegov(grupo)
    catalogo = RESOURCE_GROUPS[grupo]
    solicitados = recursos or list(catalogo)

    validos: list[str] = []
    invalidos: list[str] = []

    for recurso in solicitados:
        if recurso in catalogo:
            if recurso not in validos:
                validos.append(recurso)
            continue
        if recurso not in invalidos:
            invalidos.append(recurso)

    return tuple(validos), tuple(invalidos)


def output_path_recurso(grupo: str, recurso: str, filtros: dict | None = None) -> Path:
    """Deriva o caminho relativo de saída de uma consulta do Transferegov."""

    validar_grupo_transferegov(grupo)
    assinatura = slug_filtros(filtros)
    return Path("transferegov") / grupo / recurso / f"consulta={assinatura}.json"
