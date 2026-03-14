"""Testes do menu interativo da CLI."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from cli.menu import _build_extrair_dependentes
from cli.menu import _build_obrasgov_geometrias
from cli.menu import TerminalMenu
from cli.menu import build_menu_tree


class MenuCliTestCase(unittest.TestCase):
    """Valida o contrato estrutural do menu de terminal."""

    def test_build_menu_tree_expoe_grupos_principais(self):
        """O menu principal deve apresentar os grupos esperados."""

        titulos = [item.title for item in build_menu_tree()]

        self.assertIn("Pipelines", titulos)
        self.assertIn("Cidadão de Olho", titulos)
        self.assertIn("Camara", titulos)
        self.assertIn("Portal da Transparencia", titulos)
        self.assertIn("Fontes complementares", titulos)

    def test_builder_dependentes_usa_defaults_quando_usuario_confirma(self):
        """A execucao interativa da Camara deve montar o comando com defaults."""

        with patch("builtins.input", side_effect=["", "", ""]):
            tokens = _build_extrair_dependentes()

        self.assertIsNotNone(tokens)
        self.assertEqual(tokens[:3], ["extrair-dependentes", "--endpoint", "deputados_despesas"])
        self.assertIn("--ano-inicio", tokens)
        self.assertIn("--ano-fim", tokens)

    def test_builder_geometrias_aceita_execucao_sem_limite(self):
        """O menu deve permitir usar o default do extrator sem limitador manual."""

        with patch("builtins.input", return_value=""):
            tokens = _build_obrasgov_geometrias()

        self.assertEqual(tokens, ["extrair-obrasgov-geometrias"])

    def test_builder_cancelado_retorna_none(self):
        """Cancelar um prompt deve abortar a montagem do comando."""

        with patch("builtins.input", return_value="q"):
            tokens = _build_obrasgov_geometrias()

        self.assertIsNone(tokens)

    def test_terminal_menu_monta_subprocesso_apontando_para_main(self):
        """A execucao interativa deve chamar o `main.py` do projeto."""

        menu = TerminalMenu(build_menu_tree())

        comando = menu._build_cli_command(["extrair-siop"])

        self.assertEqual(comando[0], sys.executable)
        self.assertTrue(comando[1].endswith("/main.py"))
        self.assertEqual(comando[2:], ["extrair-siop"])


if __name__ == "__main__":
    unittest.main()
