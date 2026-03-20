"""Carga e normalizacao dos documentos consultados na ANP."""

from __future__ import annotations

from typing import Iterable


def _deduplicar_cnpjs(itens: Iterable[dict]) -> list[str]:
    """Deduplica CNPJs preservando a ordem original."""

    vistos: set[str] = set()
    documentos: list[str] = []

    for item in itens:
        if item.get("tipo_documento") != "cnpj":
            continue
        doc = item.get("documento")
        if not doc or doc in vistos:
            continue
        vistos.add(doc)
        documentos.append(doc)

    return documentos


def carregar_documentos_revendedores(
    *,
    builder,
    min_ocorrencias: int | None,
    limit_fornecedores: int | None,
) -> list[str]:
    """Carrega a seed local de fornecedores e retorna apenas CNPJs validos."""

    builder.construir(min_ocorrencias=min_ocorrencias)
    fornecedores = builder.carregar()

    if limit_fornecedores is not None:
        fornecedores = fornecedores[:limit_fornecedores]

    return _deduplicar_cnpjs(fornecedores)
