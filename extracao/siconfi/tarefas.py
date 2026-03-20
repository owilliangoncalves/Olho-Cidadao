"""Helpers puros de tarefas do Siconfi."""

from __future__ import annotations

from pathlib import Path

from extracao.siconfi.filtros import normalizar_filtros_recurso
from extracao.siconfi.filtros import obter_spec_siconfi
from extracao.siconfi.filtros import validar_filtros_recurso
from utils.filtros import slug_filtros


def resolver_recursos_siconfi(recursos: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    """Resolve a lista final de recursos, removendo duplicatas e preservando ordem."""

    vistos: set[str] = set()
    selecionados: list[str] = []
    for recurso in recursos or ("entes",):
        if recurso in vistos:
            continue
        vistos.add(recurso)
        selecionados.append(recurso)
    return tuple(selecionados)


def preparar_consultas_siconfi(recursos, filtros: dict | None):
    """Resolve recursos, normaliza filtros e valida o contrato antes de extrair."""

    consultas = []
    for recurso in resolver_recursos_siconfi(recursos):
        spec = obter_spec_siconfi(recurso)
        filtros_recurso = normalizar_filtros_recurso(recurso, filtros)
        validar_filtros_recurso(recurso, filtros_recurso)
        consultas.append((recurso, spec, filtros_recurso))
    return tuple(consultas)


def output_path_recurso(recurso: str, filtros: dict) -> Path:
    """Deriva o caminho de saida persistido para um recurso do Siconfi."""

    return Path("siconfi") / recurso / f"consulta={slug_filtros(filtros)}.json"
