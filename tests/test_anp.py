"""Testes do extrator de revendedores da ANP."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from extracao.anp import RevendedoresANP
from extracao.anp import RevendedoresConfig
from extracao.anp import carregar_documentos_revendedores
from extracao.publica import ExtratorAPIPublicaBase


class _ExtratorPublicoFalsoSemEmpty(ExtratorAPIPublicaBase):
    """Stub mínimo para validar a política de `.empty` da base pública."""

    def __init__(self, respostas):
        super().__init__(orgao="anp", nome_endpoint="revendedores")
        self.respostas = list(respostas)

    def _request_publica(self, endpoint: str, params: dict | None = None, timeout=(15, 120)):
        """Retorna respostas predefinidas sem acessar a rede."""

        if not self.respostas:
            return []
        return self.respostas.pop(0)

    def executar(self):
        """Não é usado nestes testes."""


class ExtratorRevendedoresANPTestCase(unittest.TestCase):
    """Valida contratos específicos do crawler da ANP."""

    def test_config_carrega_overrides_e_defaults(self):
        """A configuracao deve combinar defaults do projeto e overrides locais."""

        with patch(
            "extracao.anp.config.obter_parametros_extrator",
            return_value={
                "datasets": ["combustivel", "glp"],
                "min_ocorrencias": 3,
                "max_workers": 5,
                "rate_limit_per_sec": 1.5,
                "max_rate_per_sec": 4.0,
            },
        ):
            cfg = RevendedoresConfig.carregar(
                min_ocorrencias=7,
                limit_fornecedores=25,
            )

        self.assertEqual(cfg.min_ocorrencias, 7)
        self.assertEqual(cfg.limit_fornecedores, 25)
        self.assertEqual(cfg.datasets, ("combustivel", "glp"))
        self.assertEqual(cfg.max_workers, 5)
        self.assertEqual(cfg.max_pending, 20)
        self.assertEqual(cfg.rate_limit_per_sec, 1.5)
        self.assertEqual(cfg.max_rate_per_sec, 4.0)

    def test_carregar_documentos_revendedores_construi_seed_aplica_limite_e_dedup(self):
        """A carga deve usar o builder local antes de deduplicar os CNPJs."""

        builder = MagicMock()
        builder.carregar.return_value = [
            {"tipo_documento": "cnpj", "documento": "111"},
            {"tipo_documento": "cnpj", "documento": "111"},
            {"tipo_documento": "cnpj", "documento": "222"},
        ]

        documentos = carregar_documentos_revendedores(
            builder=builder,
            min_ocorrencias=2,
            limit_fornecedores=2,
        )

        builder.construir.assert_called_once_with(min_ocorrencias=2)
        self.assertEqual(documentos, ["111"])

    def test_nao_reprocessa_consultas_vazias_na_anp(self):
        """Respostas vazias da ANP não devem disparar retry adicional."""

        extrator = RevendedoresANP()

        with patch.object(
            extrator,
            "_executar_tarefa_paginada",
            return_value={"status": "empty", "records": 0, "pages": 0},
        ) as mock_executar:
            extrator._executar_tarefa("combustivel", "12345678000190")

        self.assertFalse(mock_executar.call_args.kwargs["_allow_empty_retry"])
        self.assertFalse(mock_executar.call_args.kwargs["_persist_empty_marker"])

    def test_dataset_desconhecido_e_pulado_sem_chamar_api(self):
        """Datasets fora do mapa devem sair como skip sem tocar a base HTTP."""

        extrator = RevendedoresANP()

        with patch.object(extrator, "_executar_tarefa_paginada") as mock_executar:
            extrator._executar_tarefa("oleo", "12345678000190")

        mock_executar.assert_not_called()
        self.assertEqual(extrator.stats.snapshot()["skipped"], 1)

    def test_executar_usa_cfg_para_datasets_e_limites_de_execucao(self):
        """A orquestracao deve respeitar datasets e paralelismo da configuracao."""

        extrator = RevendedoresANP()
        extrator.cfg = extrator.cfg.__class__(
            min_ocorrencias=extrator.cfg.min_ocorrencias,
            limit_fornecedores=extrator.cfg.limit_fornecedores,
            max_workers=9,
            datasets=("glp",),
            rate_limit_per_sec=extrator.cfg.rate_limit_per_sec,
            max_rate_per_sec=extrator.cfg.max_rate_per_sec,
        )

        with (
            patch.object(extrator, "_carregar_documentos", return_value=["111", "222"]),
            patch("extracao.anp.executar_tarefas_limitadas") as mock_executor,
        ):
            extrator.executar()

        tarefas = list(mock_executor.call_args.args[0])
        self.assertEqual(tarefas, [("glp", "111"), ("glp", "222")])
        self.assertEqual(mock_executor.call_args.kwargs["max_workers"], 9)
        self.assertEqual(mock_executor.call_args.kwargs["max_pending"], 36)

    def test_base_publica_nao_reaproveita_empty_quando_persistencia_esta_desligada(self):
        """`.empty` residual não deve bloquear reruns quando desabilitado."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            extrator = _ExtratorPublicoFalsoSemEmpty([[]])
            original_cwd = Path.cwd()

            try:
                os.chdir(base)
                empty = base / "data/anp/revendedores/combustivel/fornecedor=123.json.empty"
                empty.parent.mkdir(parents=True, exist_ok=True)
                empty.touch()

                resumo = extrator._executar_tarefa_paginada(
                    endpoint="/v1/combustivel",
                    base_params={"cnpj": "123"},
                    relative_output_path=Path("anp/revendedores/combustivel/fornecedor=123.json"),
                    context={"dataset": "combustivel", "documento": "123"},
                    pagination={
                        "style": "page",
                        "page_param": "numeropagina",
                        "start_page": 1,
                    },
                    item_keys=("data",),
                    _allow_empty_retry=False,
                    _persist_empty_marker=False,
                )

                self.assertEqual(resumo["status"], "empty")
                self.assertFalse(empty.exists())
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
