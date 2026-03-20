"""Normalizacao e enriquecimento dos dados de despesas do Senado."""

from __future__ import annotations

from typing import Any

from utils.documentos import base_cnpj
from utils.documentos import normalizar_documento
from utils.documentos import tipo_documento


def iterar_despesas_senado(dados: Any):
    """Normaliza a estrutura da resposta em um iterador de despesas."""

    if not dados:
        return

    despesas = dados
    if isinstance(dados, dict):
        despesas = dados.get("ListaDespesas", {}).get("Despesas", [])

    if isinstance(despesas, dict):
        yield despesas
        return

    if isinstance(despesas, list):
        for item in despesas:
            if isinstance(item, dict):
                yield item


def enriquecer_registro_senado(item: dict, *, ano: int, nome_endpoint: str) -> dict:
    """Adiciona chaves derivadas uteis para joins futuros."""

    registro = dict(item)
    documento = normalizar_documento(registro.get("cpfCnpj"))

    registro["documento_fornecedor_normalizado"] = documento
    registro["tipo_documento_fornecedor"] = tipo_documento(documento)
    registro["cnpj_base_fornecedor"] = base_cnpj(documento)
    registro["orgao_origem"] = "senado"
    registro["endpoint_origem"] = nome_endpoint
    registro["ano_arquivo"] = ano

    return registro
