"""Construção de consultas SPARQL para o endpoint do SIOP."""

from __future__ import annotations

from urllib.parse import urlencode

_MEDIA_TYPE_JSON = "application/sparql-results+json"


class SiopQueryBuilder:
    """Monta strings SPARQL e verifica se ultrapassam o limite seguro de URL.

    Responsabilidade única: saber *o que perguntar* ao endpoint, sem nada
    sobre HTTP, arquivos ou transformação de dados.
    """

    def __init__(self, max_query_length: int) -> None:
        self._max_query_length = max_query_length



    def probe_ano(self, ano: int) -> str:
        """Sonda leve — verifica se o ano possui ao menos um ItemDespesa."""

        return f"""
        PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>

        SELECT ?item
        WHERE {{
          GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
            ?item a loa:ItemDespesa .
          }}
        }}
        LIMIT 1
        """

    def ids_pagina(
        self,
        ano: int,
        funcao_codigo: str,
        limit: int,
        last_item_uri: str | None = None,
    ) -> str:
        """Consulta leve que retorna apenas os URIs da página corrente."""

        filtro_cursor = (
            f'\n            FILTER(STR(?item) > "{last_item_uri}")'
            if last_item_uri
            else ""
        )

        return f"""
        PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>

        SELECT ?item
        WHERE {{
          GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
            ?item a loa:ItemDespesa .
            ?item loa:temFuncao ?funcao .
            ?funcao loa:codigo "{funcao_codigo}" .
            {filtro_cursor}
          }}
        }}
        ORDER BY ?item
        LIMIT {limit}
        """

    def detalhes_itens(self, ano: int, item_uris: list[str]) -> str:
        """Consulta detalhada para um lote pequeno de itens."""

        itens = ", ".join(f"<{uri}>" for uri in item_uris)
        return f"""
        PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT
          ?item
          ?funcao ?funcao_nome
          ?subfuncao ?subfuncao_nome
          ?programa ?programa_nome
          ?acao ?acao_nome
          ?unidade ?unidade_nome
          ?fonte ?fonte_nome
          ?gnd ?gnd_nome
          ?modalidade ?modalidade_nome
          ?elemento ?elemento_nome
          ?valorPago
          ?valorEmpenhado
          ?valorLiquidado
        WHERE {{
          GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
            ?item a loa:ItemDespesa .
            FILTER(?item IN ({itens})) .

            ?item loa:temFuncao ?funcao .
            ?funcao rdfs:label ?funcao_nome .

            ?item loa:temSubfuncao ?subfuncao .
            ?subfuncao rdfs:label ?subfuncao_nome .

            ?item loa:temPrograma ?programa .
            ?programa rdfs:label ?programa_nome .

            ?item loa:temAcao ?acao .
            ?acao rdfs:label ?acao_nome .

            ?item loa:temUnidadeOrcamentaria ?unidade .
            ?unidade rdfs:label ?unidade_nome .

            ?item loa:temFonteRecursos ?fonte .
            ?fonte rdfs:label ?fonte_nome .

            ?item loa:temGND ?gnd .
            ?gnd rdfs:label ?gnd_nome .

            ?item loa:temModalidadeAplicacao ?modalidade .
            ?modalidade rdfs:label ?modalidade_nome .

            ?item loa:temElementoDespesa ?elemento .
            ?elemento rdfs:label ?elemento_nome .

            ?item loa:valorPago ?valorPago .
            ?item loa:valorEmpenhado ?valorEmpenhado .
            ?item loa:valorLiquidado ?valorLiquidado .
          }}
        }}
        ORDER BY ?item
        """



    def excede_limite_url(self, query: str) -> bool:
        """Indica se a query ultrapassa o limite seguro para requisições GET."""

        estimado = urlencode(
            {
                "query": query,
                "format": _MEDIA_TYPE_JSON,
                "output": _MEDIA_TYPE_JSON,
            }
        )
        return len(estimado) > self._max_query_length