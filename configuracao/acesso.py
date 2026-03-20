"""Acesso centralizado a configuracoes brutas e tipadas do projeto."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
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
    """Normaliza nomes vindos da CLI para o formato do TOML."""

    return nome.replace("-", "_")


def _obter_mapa_tipado(secao: str) -> dict[str, Any]:
    """Retorna a secao tipada desejada da configuracao carregada."""

    return cast(dict[str, Any], getattr(obter_config(), secao))


def _obter_item_tipado(secao: str, nome: str) -> Any:
    """Obtém um item tipado de uma seção nomeada da configuração."""

    return _obter_mapa_tipado(secao)[nome]


def _obter_parametros_configurados(secao: str, nome: str) -> dict[str, Any]:
    """Obtém um bloco operacional usando normalização de nome."""

    return obter_configuracao(
        f"config.{secao}.{_normalizar_chave(nome)}",
        default={},
    )


def exportar_configuracao_dict() -> dict[str, Any]:
    """Exporta uma copia profunda da configuracao bruta."""

    return deepcopy(carregar_configuracao_bruta())


@overload
def obter_configuracao(caminho: str) -> Any:
    ...


@overload
def obter_configuracao(caminho: str | None = None, *, default: T) -> T:
    ...


def obter_configuracao(caminho: str | None = None, *, default: Any = _MISSING) -> Any:
    """Obtém um valor arbitrário da configuracao usando caminho separado por `.`."""

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
    """Retorna a configuracao tipada e validada do projeto."""

    return carregar_configuracao_tipada()


def obter_parametros_cli(nome_comando: str) -> dict[str, Any]:
    """Obtém parâmetros operacionais de um comando da CLI."""

    return _obter_parametros_configurados("cli", nome_comando)


def obter_parametros_extrator(nome: str) -> dict[str, Any]:
    """Obtém parâmetros operacionais de um extrator."""

    return _obter_parametros_configurados("extratores", nome)


def obter_parametros_pipeline(nome: str) -> dict[str, Any]:
    """Obtém parâmetros operacionais de um pipeline."""

    return _obter_parametros_configurados("pipelines", nome)


def obter_intervalo_anos_padrao() -> dict[str, Any]:
    """Obtém o bloco padrao de intervalo de anos da CLI."""

    return obter_configuracao("config.cli.intervalo_anos", default={})


def obter_configuracao_endpoint(nome_endpoint: str) -> dict[str, Any]:
    """Exporta a configuracao tipada de um endpoint como dict."""

    return asdict(_obter_item_tipado("endpoints", nome_endpoint))


def obter_url_endpoint(nome_endpoint: str) -> str:
    """Obtém apenas a URL principal de um endpoint configurado."""

    return _obter_item_tipado("endpoints", nome_endpoint).endpoint


def obter_configuracao_pipeline(nome_pipeline: str) -> dict[str, Any]:
    """Exporta a configuracao tipada de um pipeline como dict."""

    return asdict(_obter_item_tipado("pipelines", nome_pipeline))
