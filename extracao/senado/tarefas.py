"""Helpers puros de orquestracao do Senado."""

from __future__ import annotations


def iterar_anos_senado(ano_inicio: int, ano_fim: int):
    """Itera os anos do mais recente para o mais antigo."""

    return range(ano_fim, ano_inicio - 1, -1)


def contador_por_status(status: str) -> str:
    """Normaliza o status de um ano para o contador agregado."""

    if status == "success":
        return "completed"
    if status in {"skipped", "skipped_empty"}:
        return "skipped"
    if status == "empty":
        return "empty"
    return "failed"
