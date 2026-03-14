"""Testes para a construção e parsing da CLI principal."""

from __future__ import annotations

import unittest
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from datetime import date
from io import StringIO

from main import build_parser
from main import main
from main import parse_data_iso


class MainCliTestCase(unittest.TestCase):
    """Valida contratos básicos da CLI pública do projeto."""

    def test_parse_data_iso_converte_para_date(self):
        """Datas ISO válidas devem ser convertidas para objetos `date`."""

        self.assertEqual(parse_data_iso("2026-03-12"), date(2026, 3, 12))

    def test_build_parser_configura_intervalo_padrao_da_camara(self):
        """A CLI da Câmara não deve sobrescrever os defaults do pipeline."""

        parser = build_parser()
        args = parser.parse_args(["rodar-pipeline"])

        self.assertEqual(args.comando, "rodar-pipeline")
        self.assertIsNone(args.ano_inicio)
        self.assertIsNone(args.ano_fim)

    def test_build_parser_expoe_menu_interativo(self):
        """O menu interativo deve estar disponível por comando direto."""

        parser = build_parser()
        args = parser.parse_args(["menu"])

        self.assertEqual(args.comando, "menu")

    def test_build_parser_expoe_alias_abrir_menu(self):
        """O alias em português deve abrir o mesmo menu interativo."""

        parser = build_parser()
        args = parser.parse_args(["abrir-menu"])

        self.assertEqual(args.comando, "abrir-menu")

    def test_build_parser_expoe_comando_cidadao_de_olho(self):
        """A CLI deve conseguir iniciar a aplicacao publica em Loco.rs."""

        parser = build_parser()
        args = parser.parse_args(["servir-cidadao-de-olho", "--ambiente", "production"])

        self.assertEqual(args.comando, "servir-cidadao-de-olho")
        self.assertEqual(args.ambiente, "production")
        self.assertFalse(args.release)

    def test_build_parser_expoe_alias_abrir_cidadao_de_olho(self):
        """O alias em português deve apontar para a mesma aplicacao publica."""

        parser = build_parser()
        args = parser.parse_args(["abrir-cidadao-de-olho", "--release"])

        self.assertEqual(args.comando, "abrir-cidadao-de-olho")
        self.assertTrue(args.release)

    def test_build_parser_preserva_flags_do_pipeline_paralelo(self):
        """A CLI paralela deve aceitar overrides sem matar a config base."""

        parser = build_parser()
        args = parser.parse_args(
            [
                "rodar-paralelo",
                "--ano-inicio",
                "2023",
                "--ano-fim",
                "2026",
                "--pncp-data-inicial",
                "2025-01-01",
                "--pncp-data-final",
                "2025-12-31",
                "--sem-siop",
            ]
        )

        self.assertEqual(args.comando, "rodar-paralelo")
        self.assertEqual(args.ano_inicio, 2023)
        self.assertEqual(args.ano_fim, 2026)
        self.assertEqual(args.pncp_data_inicial, "2025-01-01")
        self.assertEqual(args.pncp_data_final, "2025-12-31")
        self.assertFalse(args.incluir_siop)

    def test_build_parser_pipeline_paralelo_usa_none_quando_override_ausente(self):
        """O pipeline paralelo deve delegar defaults ao etl-config.toml."""

        parser = build_parser()
        args = parser.parse_args(["rodar-paralelo"])

        self.assertEqual(args.comando, "rodar-paralelo")
        self.assertIsNone(args.ano_inicio)
        self.assertIsNone(args.ano_fim)
        self.assertIsNone(args.pncp_data_inicial)
        self.assertIsNone(args.pncp_data_final)
        self.assertIsNone(args.max_workers)
        self.assertIsNone(args.incluir_camara)
        self.assertIsNone(args.incluir_siconfi)

    def test_build_parser_configura_pipeline_completo(self):
        """O comando completo deve expor overrides sem esconder a config base."""

        parser = build_parser()
        args = parser.parse_args(
            [
                "rodar-pipeline-completo",
                "--ano-inicio",
                "2020",
                "--ano-fim",
                "2026",
                "--max-workers",
                "6",
                "--sem-portal",
            ]
        )

        self.assertEqual(args.comando, "rodar-pipeline-completo")
        self.assertEqual(args.ano_inicio, 2020)
        self.assertEqual(args.ano_fim, 2026)
        self.assertEqual(args.max_workers, 6)
        self.assertFalse(args.incluir_portal)

    def test_main_retornna_codigo_2_para_filtros_invalidos_do_siconfi(self):
        """Consultas Siconfi incompletas devem falhar cedo com erro de uso."""

        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                main(
                    [
                        "extrair-siconfi",
                        "--recursos",
                        "msc_orcamentaria",
                        "--filtro",
                        "id_ente=3550308",
                    ]
                )

        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
