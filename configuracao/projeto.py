
"""
Re-exporta funções de outros módulos de configuração para manter compatibilidade.

Este arquivo consolida as importações públicas, mas cada função
tem sua responsabilidade única definida em módulos especializados:
- carregador.py: carregar e gerenciar cache de configuração
- acessor_config.py: acessar valores de configuração
- acessor_endpoint.py: acessar configurações de endpoints
- acessor_pipeline.py: acessar configurações de pipelines
- resolutor_data.py: resolver datas
"""

from __future__ import annotations


# Re-exporta para compatibilidade com código existente
from configuracao.carregador import (
    PROJECT_ROOT,
    CONFIG_PATH,
    carregar_configuracao_bruta,
    carregar_configuracao_tipada,
    recarregar_configuracao,
)
from configuracao.config import (
    exportar_configuracao_dict,
    obter_configuracao,
    obter_config,
    obter_parametros_cli,
    obter_parametros_extrator,
    obter_parametros_pipeline,
    obter_intervalo_anos_padrao,
)
from configuracao.resolutor_data import (
    resolver_data_configurada,
    resolver_data_configurada_iso,
)

__all__ = [
    "PROJECT_ROOT",
    "CONFIG_PATH",
    "carregar_configuracao_bruta",
    "carregar_configuracao_tipada",
    "recarregar_configuracao",
    "exportar_configuracao_dict",
    "obter_configuracao",
    "obter_config",
    "obter_parametros_cli",
    "obter_parametros_extrator",
    "obter_parametros_pipeline",
    "obter_intervalo_anos_padrao",
    "resolver_data_configurada",
    "resolver_data_configurada_iso",
]
