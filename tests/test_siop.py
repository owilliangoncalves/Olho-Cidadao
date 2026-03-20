"""Testes do pacote SIOP."""

from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from extracao.siop import SIOP
from extracao.siop import SiopConfig
from extracao.siop.arquivos import SiopArquivos
from extracao.siop.estado import SiopEstadoRepositorio
from extracao.siop.paginador import SiopPaginador
from extracao.siop.queries import SiopQueryBuilder
from extracao.siop.tarefas import anos_priorizados
from extracao.siop.transformador import SiopTransformador


class _FakeResponse:
    """Simula o payload de resposta anexado a um erro HTTP."""

    def __init__(self, status_code: int):
        self.status_code = status_code


class _FakeHttpError(Exception):
    """Simula um HTTPError com atributo `response`."""

    def __init__(self, status_code: int):
        super().__init__(f"status={status_code}")
        self.response = _FakeResponse(status_code)


class SiopConfigTestCase(unittest.TestCase):
    """Valida o contrato de configuração do pacote."""

    def test_carregar_aplica_defaults_do_pacote(self):
        """Campos ausentes devem cair nos defaults locais do SIOP."""

        with patch(
            "extracao.siop.config.obter_parametros_extrator",
            return_value={"funcoes_orcamentarias": ["01", "02"]},
        ):
            cfg = SiopConfig.carregar()

        self.assertEqual(cfg.funcoes_orcamentarias, ("01", "02"))
        self.assertEqual(cfg.max_workers_particoes, 6)
        self.assertEqual(cfg.page_size_inicial, 400)
        self.assertEqual(cfg.page_size_minima, 50)
        self.assertEqual(cfg.detail_batch_size, 100)
        self.assertEqual(cfg.max_workers_detalhes, 2)


class SiopHelpersTestCase(unittest.TestCase):
    """Valida helpers puros usados pela orquestração."""

    def test_anos_priorizados_prioriza_ano_fechado_e_corrente(self):
        """A fila deve começar pelo ano fechado e depois o ano atual."""

        fila = anos_priorizados([2025, 2022, 2024, 2022], ano_atual=2025)

        self.assertEqual(fila[:3], [2024, 2025, 2022])
        self.assertEqual(len(fila), len(set(fila)))
        self.assertTrue(all(ano >= 2010 for ano in fila))


class SiopQueryBuilderTestCase(unittest.TestCase):
    """Valida a montagem das consultas SPARQL."""

    def setUp(self):
        """Cria uma instância reutilizável do query builder."""

        self.builder = SiopQueryBuilder(max_query_length=7000)

    def test_query_ids_filtra_funcao_por_codigo_sem_offset(self):
        """A consulta de IDs deve filtrar pelo código da função e usar seek."""

        query = self.builder.ids_pagina(2025, "01", 400)

        self.assertIn('?funcao loa:codigo "01" .', query)
        self.assertNotIn("OFFSET", query)
        self.assertNotIn("VALUES ?funcao", query)

    def test_query_ids_usa_cursor_quando_last_item_uri_existe(self):
        """A paginação deve usar `last_item_uri` sem recorrer a OFFSET."""

        query = self.builder.ids_pagina(
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

    def test_query_detalhes_usa_filter_in_em_vez_de_values(self):
        """A consulta de detalhes deve usar `FILTER IN` para os itens."""

        query = self.builder.detalhes_itens(
            2025,
            [
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100",
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/101",
            ],
        )

        self.assertIn("FILTER(?item IN (", query)
        self.assertNotIn("VALUES ?item", query)


class SiopPaginadorTestCase(unittest.TestCase):
    """Valida paginação e enriquecimento dos registros do SIOP."""

    def _novo_paginador(self, *, cliente=None, query_builder=None):
        return SiopPaginador(
            cliente=cliente or MagicMock(),
            query_builder=query_builder or SiopQueryBuilder(max_query_length=7000),
            transformador=SiopTransformador(),
            page_size_inicial=400,
            page_size_minima=50,
            detail_batch_size=1,
            max_workers_detalhes=3,
        )

    def test_busca_ids_nao_reduz_page_size_quando_api_retornou_400(self):
        """Erros 400 devem falhar cedo na consulta leve."""

        cliente = MagicMock()
        cliente.fazer_requisicao.side_effect = _FakeHttpError(400)
        paginador = self._novo_paginador(cliente=cliente)

        with self.assertRaises(_FakeHttpError):
            paginador.buscar_ids_pagina(2025, "01", None, 400)

        self.assertEqual(cliente.fazer_requisicao.call_count, 1)

    def test_lote_de_detalhes_e_dividido_antes_de_estourar_url(self):
        """O lote deve ser dividido antes de disparar uma query grande demais."""

        cliente = MagicMock()
        cliente.fazer_requisicao.return_value = {"results": {"bindings": []}}
        query_builder = MagicMock()
        query_builder.detalhes_itens.side_effect = lambda _ano, uris: " ".join(uris)
        query_builder.excede_limite_url.side_effect = lambda query: query.count("ItemDespesa/") > 1
        paginador = self._novo_paginador(cliente=cliente, query_builder=query_builder)

        paginador.buscar_detalhes_lote(
            2025,
            [
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100",
                "http://orcamento.dados.gov.br/id/2025/ItemDespesa/101",
            ],
        )

        self.assertEqual(cliente.fazer_requisicao.call_count, 2)

    def test_coletar_registros_mantem_ordem_original_das_uris(self):
        """A ordem final deve espelhar a ordem dos URIs de entrada."""

        paginador = self._novo_paginador()

        def _lote_fake(_ano, uris):
            time.sleep(0.01)
            return [{"item": {"value": uris[0]}}]

        uris = [
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/10",
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/20",
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/30",
        ]

        with patch.object(paginador, "buscar_detalhes_lote", side_effect=_lote_fake):
            registros = paginador.coletar_registros_detalhados(2025, uris)

        self.assertEqual([registro["uri_item"] for registro in registros], uris)


class SiopEstadoRepositorioTestCase(unittest.TestCase):
    """Valida a persistência e reconciliação de checkpoints."""

    def test_reconciliacao_usa_ultima_uri_do_tmp_como_cursor(self):
        """Partições retomadas devem derivar o cursor da última linha gravada."""

        with tempfile.TemporaryDirectory() as tempdir:
            arquivos = SiopArquivos(Path(tempdir) / "siop", Path(tempdir) / "_estado" / "siop")
            repo = SiopEstadoRepositorio(arquivos=arquivos, page_size_inicial=400)
            tmp_path = arquivos.tmp_particao(2025, "02")
            tmp_path.parent.mkdir(parents=True, exist_ok=True)

            with open(tmp_path, "w", encoding="utf-8") as arquivo:
                json.dump({"uri_item": "http://orcamento.dados.gov.br/id/2025/ItemDespesa/100"}, arquivo)
                arquivo.write("\n")
                json.dump({"uri_item": "http://orcamento.dados.gov.br/id/2025/ItemDespesa/21772"}, arquivo)
                arquivo.write("\n")

            estado = repo.inicial()
            estado["status"] = "running"
            reconciliado = repo.reconciliar_com_tmp(2025, "02", estado)

        self.assertEqual(reconciliado["records"], 2)
        self.assertEqual(reconciliado["offset"], 2)
        self.assertEqual(
            reconciliado["last_item_uri"],
            "http://orcamento.dados.gov.br/id/2025/ItemDespesa/21772",
        )

    def test_ultima_uri_item_tmp_arquivo_vazio(self):
        """Arquivo temporário vazio deve retornar `None` sem lançar erro."""

        with tempfile.TemporaryDirectory() as tempdir:
            arquivos = SiopArquivos(Path(tempdir) / "siop", Path(tempdir) / "_estado" / "siop")
            repo = SiopEstadoRepositorio(arquivos=arquivos, page_size_inicial=400)
            tmp_path = arquivos.tmp_particao(2025, "01")
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.touch()

            resultado = repo._ultima_uri_item_tmp(tmp_path)

        self.assertIsNone(resultado)


class SIOPTestCase(unittest.TestCase):
    """Valida a orquestração pública do pacote."""

    def test_fachada_publica_exporta_orquestrador_do_pacote(self):
        """A classe pública deve se apresentar como parte de `extracao.siop`."""

        self.assertEqual(SIOP.__module__, "extracao.siop")

    def test_extrair_ano_executa_particoes_em_paralelo(self):
        """Partições devem ser processadas em paralelo, não em série."""

        extrator = SIOP()
        extrator.funcoes_orcamentarias = tuple(str(i).zfill(2) for i in range(1, 7))
        extrator.cfg = SimpleNamespace(max_workers_particoes=6)

        lock = threading.Lock()
        ativas = [0]
        pico = [0]

        def _particao_fake(_ano, _funcao, **_kwargs):
            with lock:
                ativas[0] += 1
                pico[0] = max(pico[0], ativas[0])
            time.sleep(0.05)
            with lock:
                ativas[0] -= 1
            return {"status": "success", "records": 1, "pages": 1}

        arquivo_empty_mock = MagicMock()
        arquivo_empty_mock.exists.return_value = False

        with (
            patch.object(extrator._arquivos, "ano_pronto", return_value=False),
            patch.object(extrator._arquivos, "empty_ano", return_value=arquivo_empty_mock),
            patch.object(extrator._cliente, "ano_tem_dados", return_value=True),
            patch.object(extrator, "_extrair_particao", side_effect=_particao_fake),
            patch.object(
                extrator,
                "_mesclar_particoes_ano",
                return_value={"status": "success", "records": 6, "pages": 0},
            ),
        ):
            extrator._extrair_ano(2025)

        self.assertGreater(pico[0], 1)

    def test_extrair_ano_nao_aborta_quando_particao_falha(self):
        """Falhas em uma partição não devem abortar o ano inteiro."""

        extrator = SIOP()
        extrator.funcoes_orcamentarias = ("01", "02", "03")
        extrator.cfg = SimpleNamespace(max_workers_particoes=3)
        funcoes_processadas: list[str] = []

        def _particao_seletiva(_ano, funcao, **_kwargs):
            funcoes_processadas.append(funcao)
            if funcao == "02":
                raise RuntimeError("falha simulada")
            return {"status": "success", "records": 1, "pages": 1}

        arquivo_empty_mock = MagicMock()
        arquivo_empty_mock.exists.return_value = False

        with (
            patch.object(extrator._arquivos, "ano_pronto", return_value=False),
            patch.object(extrator._arquivos, "empty_ano", return_value=arquivo_empty_mock),
            patch.object(extrator._cliente, "ano_tem_dados", return_value=True),
            patch.object(extrator, "_extrair_particao", side_effect=_particao_seletiva),
            patch.object(
                extrator,
                "_mesclar_particoes_ano",
                return_value={"status": "success", "records": 2, "pages": 0},
            ),
        ):
            resultado = extrator._extrair_ano(2025)

        self.assertEqual(sorted(funcoes_processadas), ["01", "02", "03"])
        self.assertEqual(resultado["status"], "success")


if __name__ == "__main__":
    unittest.main()
