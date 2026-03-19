"""Responsabilidade única: acessar configurações de endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from configuracao.config import obter_config


def obter_configuracao_endpoint(nome_endpoint: str) -> dict[str, Any]:
    """Obtém configuração completa de um endpoint."""
    cfg = obter_config().endpoints[nome_endpoint]
    return asdict(cfg)


def obter_url_endpoint(nome_endpoint: str) -> str:
    """Obtém URL de um endpoint."""
    return obter_config().endpoints[nome_endpoint].endpoint
