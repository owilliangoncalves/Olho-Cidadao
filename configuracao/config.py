"""Responsabilidade única: acessar e recuperar valores de configuração."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypeVar, cast, overload

from configuracao.carregador import (
    carregar_configuracao_bruta,
    carregar_configuracao_tipada,
)
from configuracao.excecoes import ChaveConfiguracaoNaoEncontrada
from configuracao.modelos import ProjetoConfig

T = TypeVar("T")
_MISSING = object()


def _normalizar_chave(nome: str) -> str:
    """Normaliza nome de chave (converte hífens em underscores)."""
    return nome.replace("-", "_")


def exportar_configuracao_dict() -> dict[str, Any]:
    """Exporta cópia profunda da configuração bruta."""
    return deepcopy(carregar_configuracao_bruta())


@overload
def obter_configuracao(caminho: str) -> Any:
    ...


@overload
def obter_configuracao(caminho: str | None = None, *, default: T) -> T:
    ...


def obter_configuracao(caminho: str | None = None, *, default: Any = _MISSING) -> Any:
    """Obtém valor de configuração por caminho (ex: 'config.cli.meu_comando')."""
    valor: Any = carregar_configuracao_bruta()

    if caminho:
        for segmento in caminho.split("."):
            if not isinstance(valor, dict) or segmento not in valor:
                if default is _MISSING:
                    raise ChaveConfiguracaoNaoEncontrada(
                        f"Configuração '{caminho}' não encontrada."
                    )
                return deepcopy(default)
            valor = cast(Any, valor[segmento])

    return deepcopy(valor)


def obter_config() -> ProjetoConfig:
    """Obtém a configuração tipada e validada."""
    return carregar_configuracao_tipada()


def obter_parametros_cli(nome_comando: str) -> dict[str, Any]:
    """Obtém parâmetros de um comando da CLI."""
    return obter_configuracao(
        f"config.cli.{_normalizar_chave(nome_comando)}",
        default={},
    )


def obter_parametros_extrator(nome: str) -> dict[str, Any]:
    """Obtém parâmetros de um extrator."""
    return obter_configuracao(
        f"config.extratores.{_normalizar_chave(nome)}",
        default={},
    )


def obter_parametros_pipeline(nome: str) -> dict[str, Any]:
    """Obtém parâmetros de um pipeline."""
    return obter_configuracao(
        f"config.pipelines.{_normalizar_chave(nome)}",
        default={},
    )


def obter_intervalo_anos_padrao() -> dict[str, Any]:
    """Obtém intervalo de anos padrão da configuração."""
    return obter_configuracao("config.cli.intervalo_anos", default={})
