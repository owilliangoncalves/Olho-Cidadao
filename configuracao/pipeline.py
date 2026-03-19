"""Responsabilidade única: acessar configurações de pipelines."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from configuracao.config import obter_config


def obter_configuracao_pipeline(nome_pipeline: str) -> dict[str, Any]:
    """Obtém configuração completa de um pipeline."""
    cfg = obter_config().pipelines[nome_pipeline]
    return asdict(cfg)
