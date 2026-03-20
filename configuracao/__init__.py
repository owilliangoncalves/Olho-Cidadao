"""Fachada publica da camada de configuracao do projeto.

Este pacote expõe um ponto único para carregamento, acesso tipado e
resolução de datas.
"""

from __future__ import annotations

from configuracao.acesso import exportar_configuracao_dict
from configuracao.acesso import obter_config
from configuracao.acesso import obter_configuracao
from configuracao.acesso import obter_configuracao_endpoint
from configuracao.acesso import obter_configuracao_pipeline
from configuracao.acesso import obter_intervalo_anos_padrao
from configuracao.acesso import obter_parametros_cli
from configuracao.acesso import obter_parametros_extrator
from configuracao.acesso import obter_parametros_pipeline
from configuracao.acesso import obter_url_endpoint
from configuracao.carregador import CONFIG_PATH
from configuracao.carregador import PROJECT_ROOT
from configuracao.carregador import carregar_configuracao_bruta
from configuracao.carregador import carregar_configuracao_tipada
from configuracao.carregador import recarregar_configuracao
from configuracao.excecoes import ArquivoConfiguracaoNaoEncontrado
from configuracao.excecoes import ChaveConfiguracaoNaoEncontrada
from configuracao.excecoes import ConfiguracaoInvalida
from configuracao.modelos import ConfigOperacional
from configuracao.modelos import EndpointConfig
from configuracao.modelos import PipelineConfig
from configuracao.modelos import ProjetoConfig
from configuracao.resolutor_data import resolver_data_configurada
from configuracao.resolutor_data import resolver_data_configurada_iso

urls = exportar_configuracao_dict()

__all__ = [
    "ArquivoConfiguracaoNaoEncontrado",
    "CONFIG_PATH",
    "ChaveConfiguracaoNaoEncontrada",
    "ConfigOperacional",
    "ConfiguracaoInvalida",
    "EndpointConfig",
    "PROJECT_ROOT",
    "PipelineConfig",
    "ProjetoConfig",
    "carregar_configuracao_bruta",
    "carregar_configuracao_tipada",
    "exportar_configuracao_dict",
    "obter_config",
    "obter_configuracao",
    "obter_configuracao_endpoint",
    "obter_configuracao_pipeline",
    "obter_intervalo_anos_padrao",
    "obter_parametros_cli",
    "obter_parametros_extrator",
    "obter_parametros_pipeline",
    "obter_url_endpoint",
    "recarregar_configuracao",
    "resolver_data_configurada",
    "resolver_data_configurada_iso",
    "urls",
]
