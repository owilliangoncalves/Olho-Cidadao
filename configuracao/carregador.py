"""Responsabilidade única: carregar e gerenciar cache de configurações."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import tomllib

from configuracao.excecoes import ArquivoConfiguracaoNaoEncontrado
from configuracao.modelos import ProjetoConfig
from configuracao.validacao import construir_config_projeto

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "etl-config.toml"

if not CONFIG_PATH.exists():
    raise ArquivoConfiguracaoNaoEncontrado(
        f"Arquivo de configuração não encontrado: {CONFIG_PATH}. "
        "Crie o etl-config.toml na raiz do projeto."
    )


@lru_cache(maxsize=1)
def carregar_configuracao_bruta() -> dict[str, Any]:
    """Carrega a configuração bruta do arquivo TOML."""
    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)
    if not isinstance(data, dict):
        raise TypeError("O arquivo TOML raiz deve ser um objeto/tabela.")
    return data


@lru_cache(maxsize=1)
def carregar_configuracao_tipada() -> ProjetoConfig:
    """Carrega e valida a configuração tipada."""
    raw = carregar_configuracao_bruta()
    return construir_config_projeto(raw)


def recarregar_configuracao() -> None:
    """Limpa o cache e força recarregamento da próxima vez."""
    carregar_configuracao_bruta.cache_clear()
    carregar_configuracao_tipada.cache_clear()
