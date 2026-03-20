"""Testes do pipeline paralelo e sua leitura declarativa de configuração."""

from __future__ import annotations

from datetime import date
import unittest
from unittest.mock import patch

from infra.errors import UserInputError
from pipeline import PipelineParalelo


class PipelineParaleloTestCase(unittest.TestCase):
    """Valida contratos de configuração e preflight do pipeline paralelo."""

    def test_respeita_fontes_do_etl_config_quando_cli_nao_sobrescreve(self):
        """Flags omitidas na CLI devem deixar a decisão no arquivo TOML."""

        config = {
            "ano_inicio": 2020,
            "ano_fim": 2022,
            "pncp_data_inicial": date(2025, 1, 1),
            "pncp_data_final": date(2025, 1, 31),
            "max_workers": 3,
            "fontes": {
                "camara": False,
                "senado": True,
                "siop": False,
                "ibge": True,
                "pncp": True,
                "transferegov": False,
                "obrasgov": True,
                "siconfi": False,
            },
            "senado_endpoint": "ceaps",
            "ibge_datasets": ["regioes"],
            "siconfi_recursos": ["entes"],
            "siconfi_filtros": {"an_exercicio": 2024},
            "siconfi_tamanho_pagina": 1000,
        }

        with patch("pipeline.config.obter_parametros_pipeline", return_value=config):
            pipeline = PipelineParalelo()

        self.assertFalse(pipeline.incluir_camara)
        self.assertTrue(pipeline.incluir_senado)
        self.assertFalse(pipeline.incluir_siop)
        self.assertTrue(pipeline.incluir_ibge)
        self.assertFalse(pipeline.incluir_transferegov)
        self.assertFalse(pipeline.incluir_siconfi)
        self.assertEqual(pipeline.siconfi_filtros, {"an_exercicio": 2024})

    def test_falha_cedo_quando_max_workers_ausente(self):
        """Configuração incompleta deve gerar erro de uso claro."""

        config = {
            "ano_inicio": 2020,
            "ano_fim": 2022,
            "pncp_data_inicial": date(2025, 1, 1),
            "pncp_data_final": date(2025, 1, 31),
            "fontes": {},
        }

        with patch("pipeline.config.obter_parametros_pipeline", return_value=config):
            with self.assertRaises(UserInputError):
                PipelineParalelo()

    def test_falha_cedo_quando_intervalo_pncp_e_invalido(self):
        """Erros de datas do PNCP devem usar UserInputError."""

        config = {
            "ano_inicio": 2020,
            "ano_fim": 2022,
            "pncp_data_inicial": date(2025, 2, 1),
            "pncp_data_final": date(2025, 1, 31),
            "max_workers": 2,
            "fontes": {},
        }

        with patch("pipeline.config.obter_parametros_pipeline", return_value=config):
            with self.assertRaises(UserInputError):
                PipelineParalelo()


if __name__ == "__main__":
    unittest.main()
