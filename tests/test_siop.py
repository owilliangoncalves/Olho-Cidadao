"""Testes do extrator do SIOP."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extracao.siop.extrator_siop import ExtratorSIOP


class _FakeResponse:
    """Simula a resposta HTTP acoplada a uma excecao."""

    def __init__(self, status_code: int):
        self.status_code = status_code


class _FakeHttpError(Exception):
    """Simula um HTTPError com atributo `response`."""

    def __init__(self, status_code: int):
        super().__init__(f"status={status_code}")
        self.response = _FakeResponse(status_code)


class ExtratorSIOPTestCase(unittest.TestCase):
    """Valida contratos importantes do crawler do SIOP."""

    def test_query_ids_filtra_funcao_por_codigo_sem_uri_hardcoded(self):
        """A consulta de IDs deve usar o codigo da funcao no grafo do ano."""

        extrator = ExtratorSIOP()

        query = extrator._query_ids_item_despesa(2025, "01", 400)

        self.assertIn('?funcao loa:codigo "01" .', query)
        self.assertNotIn("VALUES ?funcao", query)
        self.assertNotIn("rdfs:label ?funcao_nome", query)
        self.assertNotIn("OFFSET", query)

    def test_query_ids_usa_cursor_quando_last_item_uri_existe(self):
        """A paginação deve usar seek por `last_item_uri`, sem `OFFSET`."""

        extrator = ExtratorSIOP()

        query = extrator._query_ids_item_despesa(
            2025,
            "01",
            400,
            last_item_uri="http://orcamento.dados.gov.br/id/2025/ItemDespesa/21772",
        )

        self.assertIn(
            'FILTER(STR(?item) > "http://orcamento.dados.gov.br/id/2025/ItemDespesa/21772")',
            query,
        )
        self.assertNotIn("OFFSET", query)

    def test_query_detalhes_usa_filter_in_em_vez_de_values_item(self):
        """A consulta de detalhes deve usar `FILTER IN`, nao `VALUES ?item`."""

        extrator = ExtratorSIOP()

        query = extrator._query_detalhes_itens(
            2025,
            [
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100",
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/101",
            ],
        )

        self.assertIn("FILTER(?item IN (", query)
        self.assertNotIn("VALUES ?item", query)

    def test_busca_ids_nao_reduz_page_size_quando_api_retornou_400(self):
        """Erros 400 devem falhar cedo na consulta leve."""

        extrator = ExtratorSIOP()
        chamadas = []

        def _falhar(*_args, **_kwargs):
            chamadas.append("tentativa")
            raise _FakeHttpError(400)

        extrator._fazer_requisicao_sparql = _falhar  # type: ignore[method-assign]

        with self.assertRaises(_FakeHttpError):
            extrator._buscar_ids_pagina(2025, "01", None, 400)

        self.assertEqual(len(chamadas), 1)

    def test_lote_de_detalhes_e_dividido_antes_de_estourar_url(self):
        """O lote deve ser reduzido preventivamente quando a URL ficaria grande."""

        extrator = ExtratorSIOP()
        chamadas = []

        def _ok(query, ano=None, timeout=None):
            chamadas.append(query)
            return {"results": {"bindings": []}}

        extrator._fazer_requisicao_sparql = _ok  # type: ignore[method-assign]
        extrator._query_excede_limite_url = lambda query: query.count("ItemDespesa/") > 1  # type: ignore[method-assign]
        extrator._buscar_detalhes_lote(
            2025,
            [
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100",
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/101",
            ],
        )

        self.assertEqual(len(chamadas), 2)

    def test_requisicao_sparql_usa_retry_curto_local_ao_siop(self):
        """O SIOP deve usar retry curto sem impor regra global ao cliente HTTP."""

        extrator = ExtratorSIOP()

        with patch("extracao.siop.extrator_siop.http_client.get", return_value={"results": {"bindings": []}}) as mock_get:
            extrator._fazer_requisicao_sparql("SELECT * WHERE { ?s ?p ?o }", ano=2025)

        self.assertEqual(mock_get.call_args.kwargs["retries"], 1)

    def test_reconciliacao_usa_ultima_uri_do_tmp_como_cursor(self):
        """Partições retomadas devem derivar o cursor da última linha gravada."""

        extrator = ExtratorSIOP()

        with tempfile.TemporaryDirectory() as tempdir:
            cwd_original = os.getcwd()
            os.chdir(tempdir)
            try:
                tmp_path = Path("data/orcamento_item_despesa/_particoes/ano=2025/funcao=02.json.tmp")
                tmp_path.parent.mkdir(parents=True, exist_ok=True)

                with open(tmp_path, "w", encoding="utf-8") as arquivo:
                    json.dump({"uri_item": "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100"}, arquivo)
                    arquivo.write("\n")
                    json.dump({"uri_item": "http://orcamento.dados.gov.br/id/2025/ItemDespesa/21772"}, arquivo)
                    arquivo.write("\n")

                estado = extrator._estado_inicial()
                estado["status"] = "running"
                reconciliado = extrator._reconciliar_particao_com_tmp(2025, "02", estado)
            finally:
                os.chdir(cwd_original)

        self.assertEqual(reconciliado["records"], 2)
        self.assertEqual(reconciliado["offset"], 2)
        self.assertEqual(
            reconciliado["last_item_uri"],
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/21772",
        )
