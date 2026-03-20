"""Testes do pacote de consultas públicas do PNCP."""

from __future__ import annotations

from datetime import date
import unittest
from unittest.mock import patch

from infra.errors import UserInputError
from extracao.pncp import PNCPConsulta
from extracao.pncp import PNCPConsultaConfig
from extracao.pncp.tarefas import fim_do_mes
from extracao.pncp.tarefas import iterar_anos
from extracao.pncp.tarefas import iterar_janelas_mensais
from extracao.pncp.tarefas import output_path_janela
from extracao.pncp.tarefas import output_path_pca


class PncpHelpersTestCase(unittest.TestCase):
    """Valida helpers puros usados pelo pacote do PNCP."""

    def test_fim_do_mes_resolve_fevereiro_bissexto(self):
        """O helper deve encontrar corretamente o último dia do mês."""

        self.assertEqual(fim_do_mes(date(2024, 2, 10)), date(2024, 2, 29))

    def test_iterar_janelas_mensais_recorta_intervalo(self):
        """As janelas mensais devem respeitar os limites pedidos."""

        janelas = list(
            iterar_janelas_mensais(
                date(2025, 1, 15),
                date(2025, 3, 2),
            )
        )

        self.assertEqual(
            janelas,
            [
                (date(2025, 1, 15), date(2025, 1, 31)),
                (date(2025, 2, 1), date(2025, 2, 28)),
                (date(2025, 3, 1), date(2025, 3, 2)),
            ],
        )

    def test_paths_e_anos_seguem_convencao_do_pacote(self):
        """Os helpers de saída não devem espalhar convenções no orquestrador."""

        self.assertEqual(list(iterar_anos(date(2024, 12, 31), date(2026, 1, 1))), [2024, 2025, 2026])
        self.assertEqual(
            output_path_janela("atas", date(2025, 2, 1)).as_posix(),
            "pncp/atas/ano=2025/mes=02.json",
        )
        self.assertEqual(output_path_pca(2026).as_posix(), "pncp/pca/ano=2026.json")


class PncpConsultaTestCase(unittest.TestCase):
    """Valida a orquestração pública do pacote PNCP."""

    def test_config_carrega_overrides_e_aplica_minimo(self):
        """O tamanho de página deve respeitar override e piso mínimo."""

        with patch(
            "extracao.pncp.config.obter_parametros_extrator",
            return_value={
                "page_size": 5,
                "rate_limit_per_sec": 1.5,
                "max_rate_per_sec": 3.0,
            },
        ):
            cfg = PNCPConsultaConfig.carregar(page_size=7)

        self.assertEqual(cfg.page_size, 10)
        self.assertEqual(cfg.rate_limit_per_sec, 1.5)
        self.assertEqual(cfg.max_rate_per_sec, 3.0)

    def test_executar_valida_intervalo_invalido(self):
        """A API pública deve falhar cedo quando o intervalo vier invertido."""

        extrator = PNCPConsulta()

        with self.assertRaises(UserInputError):
            extrator.executar(date(2025, 2, 1), date(2025, 1, 31))

    def test_executar_processa_contratos_atas_e_pca(self):
        """O orquestrador deve dividir mensalmente e manter PCA anual."""

        extrator = PNCPConsulta(page_size=77)

        with patch(
            "extracao.pncp.obter_url_endpoint",
            side_effect=lambda nome: {
                "pncp_contratos": "/v1/contratos",
                "pncp_atas": "/v1/atas",
                "pncp_pca": "/v1/pca/",
            }[nome],
        ):
            with patch.object(
                extrator,
                "_executar_tarefa_paginada",
                return_value={"status": "success", "records": 12},
            ) as executar:
                extrator.executar(
                    date(2025, 1, 15),
                    date(2025, 2, 2),
                    codigo_classificacao_superior="1234",
                )

        self.assertEqual(executar.call_count, 5)
        self.assertEqual(executar.call_args_list[0].kwargs["endpoint"], "/v1/contratos")
        self.assertEqual(
            executar.call_args_list[0].kwargs["relative_output_path"].as_posix(),
            "pncp/contratos/ano=2025/mes=01.json",
        )
        self.assertEqual(executar.call_args_list[2].kwargs["endpoint"], "/v1/atas")
        self.assertEqual(executar.call_args_list[4].kwargs["endpoint"], "/v1/pca/")
        self.assertEqual(
            executar.call_args_list[4].kwargs["base_params"],
            {"anoPca": 2025, "codigoClassificacaoSuperior": "1234"},
        )
        self.assertEqual(
            executar.call_args_list[4].kwargs["pagination"]["page_size"],
            77,
        )
