"""Testes do pipeline completo e sua configuração declarativa."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from infra.errors import UserInputError
from pipeline import PipelineCompleto


class PipelineCompletoTestCase(unittest.TestCase):
    """Valida precondições e leitura de configuração do pipeline completo."""

    def test_ler_configuracao_de_siconfi_do_etl_config(self):
        """O pipeline completo deve herdar recursos do `etl-config.toml`."""

        pipeline = PipelineCompleto(incluir_portal=False)

        self.assertEqual(pipeline.senado_endpoint, "ceaps")
        self.assertEqual(pipeline.ibge_datasets, ["regioes", "estados", "municipios"])
        self.assertEqual(pipeline.siconfi_recursos, ["entes"])
        self.assertEqual(pipeline.siconfi_tamanho_pagina, 1000)

    def test_preflight_rejeita_portal_sem_chave(self):
        """A falta da chave do Portal deve falhar antes da fase paralela."""

        with patch.dict("os.environ", {}, clear=True):
            pipeline = PipelineCompleto(incluir_portal=True)

            with self.assertRaises(UserInputError):
                pipeline._validar_precondicoes()

    def test_pipeline_completo_executa_fases_dependentes_na_ordem_esperada(self):
        """A orquestração deve passar pela fase de geometrias sem falhar."""

        chamadas = []
        mock_obrasgov = MagicMock()
        mock_obrasgov.executar_geometrias.side_effect = (
            lambda limit_ids=None: chamadas.append(("obrasgov_geometrias", limit_ids))
        )

        with patch.dict("os.environ", {"PORTAL_TRANSPARENCIA_API_KEY": "dummy"}, clear=True):
            with patch(
                "pipeline.PipelineParalelo.executar",
                autospec=True,
                side_effect=lambda self: chamadas.append("paralelo"),
            ):
                with patch(
                    "pipeline.PipelinePortalTransparencia.executar",
                    autospec=True,
                    side_effect=lambda self: chamadas.append("portal"),
                ):
                    with patch(
                        "pipeline.RevendedoresANP.executar",
                        autospec=True,
                        side_effect=lambda self, datasets=None: chamadas.append(
                            ("anp", tuple(datasets or []))
                        ),
                    ):
                        with patch(
                            "pipeline.ObrasGov",
                            return_value=mock_obrasgov,
                        ):
                            PipelineCompleto().executar()

        self.assertEqual(
            chamadas,
            [
                "paralelo",
                "portal",
                ("anp", ("combustivel", "glp")),
                ("obrasgov_geometrias", None),
            ],
        )


if __name__ == "__main__":
    unittest.main()
