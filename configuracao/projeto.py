"""Leitura e resolução da configuração declarativa do projeto.

Este módulo centraliza o acesso ao ``etl-config.toml``. Os consumidores do
projeto não precisam conhecer o arquivo físico; usam apenas os helpers daqui.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ETL_CONFIG_TOML = PROJECT_ROOT / "etl-config.toml"
CONFIG_PATH = ETL_CONFIG_TOML

if not CONFIG_PATH.exists():
    raise FileNotFoundError(
        f"Arquivo de configuração não encontrado: {CONFIG_PATH}. "
        "Crie o etl-config.toml na raiz do projeto."
    )

with open(CONFIG_PATH, "rb") as f:
    project_config = tomllib.load(f)

_MISSING = object()


def _normalizar_chave(nome: str) -> str:
    """Normaliza nomes lógicos para chaves estáveis no arquivo TOML."""

    return nome.replace("-", "_")


def obter_configuracao(caminho: str | None = None, *, default: Any = _MISSING) -> Any:
    """Recupera uma seção arbitrária da configuração por caminho pontuado.

    Args:
        caminho: Caminho pontuado, como ``"config.pipelines.completo"``.
        default: Valor usado quando o caminho não existe. Se omitido, lança
            ``KeyError``.

    Returns:
        Uma cópia profunda do valor configurado para evitar mutações acidentais.

    Raises:
        KeyError: Quando o caminho não existe e nenhum ``default`` foi
            informado.
    """

    valor: Any = project_config
    if caminho:
        for segmento in caminho.split("."):
            if not isinstance(valor, dict) or segmento not in valor:
                if default is _MISSING:
                    raise KeyError(
                        f"Configuração '{caminho}' não encontrada em {CONFIG_PATH.name}."
                    )
                return deepcopy(default)
            valor = valor[segmento]

    return deepcopy(valor)


def obter_parametros_cli(nome_comando: str) -> dict:
    """Recupera os defaults declarativos associados a um comando da CLI."""

    return obter_configuracao(
        f"config.cli.{_normalizar_chave(nome_comando)}",
        default={},
    )


def obter_parametros_extrator(nome: str) -> dict:
    """Recupera a configuração operacional de um extrator."""

    return obter_configuracao(
        f"config.extratores.{_normalizar_chave(nome)}",
        default={},
    )


def obter_parametros_pipeline(nome: str) -> dict:
    """Recupera defaults operacionais de um pipeline local do projeto."""

    return obter_configuracao(
        f"config.pipelines.{_normalizar_chave(nome)}",
        default={},
    )


def obter_intervalo_anos_padrao() -> dict:
    """Recupera o intervalo anual padrão compartilhado pela CLI."""

    return obter_configuracao("config.cli.intervalo_anos", default={})


def resolver_data_configurada(valor: date | str | None) -> date | None:
    """Resolve uma data configurada por literal ISO ou token declarativo.

    Tokens suportados:

    - ``today``
    - ``start_of_current_year``
    """

    if valor is None or valor == "":
        return None

    if isinstance(valor, date):
        return valor

    token = str(valor).strip()
    if token == "today":
        return date.today()
    if token == "start_of_current_year":
        return date.today().replace(month=1, day=1)

    return date.fromisoformat(token)


def resolver_data_configurada_iso(valor: date | str | None) -> str | None:
    """Resolve uma data configurada e a devolve em formato ISO."""

    resolvida = resolver_data_configurada(valor)
    return resolvida.isoformat() if resolvida else None
