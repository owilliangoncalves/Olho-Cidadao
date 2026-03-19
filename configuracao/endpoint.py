"""
Re-exporta funções de accessor para manter compatibilidade.

Originalmente este arquivo misturava acesso de endpoints e pipelines.
Agora cada um tem seu próprio módulo com SRP:
- endpoint.py: responsável por endpoints
- pipeline.py: responsável por pipelines
"""

from __future__ import annotations

# Re-exporta para compatibilidade com código existente
from configuracao.acessor_endpoint import (
    obter_configuracao_endpoint,
    obter_url_endpoint,
)
from configuracao.pipeline import (
    obter_configuracao_pipeline,
)
from configuracao.config import exportar_configuracao_dict

# Para compatibilidade com código que acessa `urls` diretamente
urls = exportar_configuracao_dict()

__all__ = [
    "obter_configuracao_endpoint",
    "obter_url_endpoint",
    "obter_configuracao_pipeline",
    "urls",
]
