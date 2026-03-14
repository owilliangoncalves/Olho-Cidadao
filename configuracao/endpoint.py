"""Fachada enxuta para endpoints e pipelines nomeados do ETL."""

from configuracao.projeto import obter_configuracao

# Mantém compatibilidade com extratores mais antigos que ainda acessam o mapa
# completo de configuração por chave, sem expor o dicionário bruto do loader.
urls = obter_configuracao()


def obter_configuracao_endpoint(nome_endpoint: str) -> dict:
    """Recupera a configuração de um endpoint declarado em `etl-config.toml`.

    Args:
        nome_endpoint: Nome lógico do endpoint no bloco `endpoints`.

    Returns:
        Dicionário de configuração associado ao endpoint.

    Raises:
        KeyError: Quando o endpoint solicitado não existe.
    """

    return obter_configuracao(f"endpoints.{nome_endpoint}")


def obter_url_endpoint(nome_endpoint: str) -> str:
    """Retorna apenas a URL/caminho configurado para um endpoint nomeado."""

    return obter_configuracao_endpoint(nome_endpoint)["endpoint"]


def obter_configuracao_pipeline(nome_pipeline: str) -> dict:
    """Recupera a configuração declarativa de um pipeline em `etl-config.toml`."""

    return obter_configuracao(f"pipelines.{nome_pipeline}")
