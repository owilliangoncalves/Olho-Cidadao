"""Testes do extrator do SIOP."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from extracao.siop.extrator import ExtratorSIOP


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

    def test_extrair_ano_executa_particoes_em_paralelo(self):
        """Partições devem ser processadas em paralelo, não em série.

        O teste mede o pico de execuções simultâneas usando um contador
        protegido por lock. Com max_workers_particoes=6 e 6 funções, o pico
        deve ser maior que 1 — confirmando paralelismo real.
        """

        extrator = ExtratorSIOP()
        lock = threading.Lock()
        ativas = [0]
        pico: list[int] = [0]

        def _particao_fake(ano, funcao, **kwargs):
            with lock:
                ativas[0] += 1
                pico[0] = max(pico[0], ativas[0])
            time.sleep(0.05)  # simula latência HTTP
            with lock:
                ativas[0] -= 1
            return {"status": "success", "records": 1, "pages": 1}

        arquivo_empty_mock = MagicMock()
        arquivo_empty_mock.exists.return_value = False

        with (
            patch.object(extrator, "_arquivo_pronto", return_value=False),
            patch.object(extrator, "_arquivo_saida", return_value=MagicMock(parent=MagicMock())),
            patch.object(extrator, "_arquivo_empty", return_value=arquivo_empty_mock),
            patch.object(extrator, "_ano_tem_dados", return_value=True),
            patch.object(extrator, "_extrair_particao", side_effect=_particao_fake),
            patch.object(
                extrator,
                "_mesclar_particoes_ano",
                return_value={"status": "success", "records": 6, "pages": 0},
            ),
        ):
            extrator.funcoes_orcamentarias = tuple(str(i).zfill(2) for i in range(1, 7))
            extrator.max_workers_particoes = 6
            extrator._extrair_ano(2025)

        self.assertGreater(pico[0], 1, "Esperado paralelismo real entre partições")

    def test_extrair_ano_nao_aborta_quando_particao_falha(self):
        """Uma falha em partição individual não deve abortar o ano inteiro."""

        extrator = ExtratorSIOP()
        funcoes_processadas: list[str] = []

        def _particao_seletiva(ano, funcao, **kwargs):
            funcoes_processadas.append(funcao)
            if funcao == "02":
                raise RuntimeError("falha simulada na funcao 02")
            return {"status": "success", "records": 1, "pages": 1}

        arquivo_empty_mock = MagicMock()
        arquivo_empty_mock.exists.return_value = False

        with (
            patch.object(extrator, "_arquivo_pronto", return_value=False),
            patch.object(extrator, "_arquivo_saida", return_value=MagicMock(parent=MagicMock())),
            patch.object(extrator, "_arquivo_empty", return_value=arquivo_empty_mock),
            patch.object(extrator, "_ano_tem_dados", return_value=True),
            patch.object(extrator, "_extrair_particao", side_effect=_particao_seletiva),
            patch.object(
                extrator,
                "_mesclar_particoes_ano",
                return_value={"status": "success", "records": 2, "pages": 0},
            ),
        ):
            extrator.funcoes_orcamentarias = ("01", "02", "03")
            extrator.max_workers_particoes = 3
            resultado = extrator._extrair_ano(2025)

        # As 3 funções foram submetidas ao pool
        self.assertEqual(sorted(funcoes_processadas), ["01", "02", "03"])
        # O ano consolidou o que havia mesmo com a falha
        self.assertEqual(resultado["status"], "success")

    def test_coletar_registros_detalhados_em_paralelo(self):
        """Lotes de detalhes devem ser buscados em paralelo (nível 2).

        Verifica que múltiplas chamadas a _buscar_detalhes_lote ocorrem
        simultaneamente quando há mais de um lote disponível.
        """

        extrator = ExtratorSIOP()
        extrator.detail_batch_size = 1   # 1 URI por lote → 3 lotes para 3 URIs
        extrator.max_workers_detalhes = 3

        lock = threading.Lock()
        ativas = [0]
        pico: list[int] = [0]

        def _lote_fake(ano, uris):
            with lock:
                ativas[0] += 1
                pico[0] = max(pico[0], ativas[0])
            time.sleep(0.03)
            with lock:
                ativas[0] -= 1
            uri = uris[0]
            return [{"item": {"value": uri}}]

        with patch.object(extrator, "_buscar_detalhes_lote", side_effect=_lote_fake):
            uris = [
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/1",
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/2",
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/3",
            ]
            registros = extrator._coletar_registros_detalhados(2025, uris)

        self.assertEqual(len(registros), 3)
        self.assertGreater(pico[0], 1, "Esperado paralelismo real entre lotes de detalhes")

    def test_coletar_registros_mantem_ordem_original_das_uris(self):
        """A ordem dos registros retornados deve espelhar a ordem dos URIs de entrada.

        Com lotes paralelos a ordem de conclusão é não-determinística; o código
        deve reconstituir a sequência original antes de devolver.
        """

        extrator = ExtratorSIOP()
        extrator.detail_batch_size = 1
        extrator.max_workers_detalhes = 3

        def _lote_fake(ano, uris):
            time.sleep(0.01)
            return [{"item": {"value": uris[0]}}]

        uris = [
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/10",
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/20",
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/30",
        ]

        with patch.object(extrator, "_buscar_detalhes_lote", side_effect=_lote_fake):
            registros = extrator._coletar_registros_detalhados(2025, uris)

        uris_resultado = [r["uri_item"] for r in registros]
        self.assertEqual(uris_resultado, uris)

    def test_ultima_uri_item_tmp_leitura_reversa(self):
        """O tail reader deve retornar a última uri_item sem ler o arquivo inteiro."""

        extrator = ExtratorSIOP()

        with tempfile.TemporaryDirectory() as tempdir:
            tmp_path = Path(tempdir) / "test.json.tmp"

            # Escreve 100 registros; a última URI deve ser a 100
            with open(tmp_path, "w", encoding="utf-8") as f:
                for i in range(1, 101):
                    json.dump({"uri_item": f"http://orcamento.dados.gov.br/id/2025/ItemDespesa/{i}"}, f)
                    f.write("\n")

            resultado = extrator._ultima_uri_item_tmp(tmp_path)

        self.assertEqual(
            resultado,
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100",
        )

    def test_ultima_uri_item_tmp_arquivo_vazio(self):
        """O tail reader deve retornar None para arquivo vazio sem lançar exceção."""

        extrator = ExtratorSIOP()

        with tempfile.TemporaryDirectory() as tempdir:
            tmp_path = Path(tempdir) / "empty.json.tmp"
            tmp_path.touch()
            resultado = extrator._ultima_uri_item_tmp(tmp_path)

        self.assertIsNone(resultado)
