"""Testes do endurecimento de parâmetros do extrator Siconfi."""

from __future__ import annotations

import unittest

from extracao.siconfi.api import ExtratorSiconfi
from infra.errors import UserInputError


class SiconfiValidationTestCase(unittest.TestCase):
    """Valida normalização e contrato mínimo de filtros do Siconfi."""

    def setUp(self):
        """Cria uma instância reutilizável do extrator sob teste."""

        self.extrator = ExtratorSiconfi()

    def test_normaliza_aliases_de_msc_orcamentaria(self):
        """Aliases comuns devem ser convertidos para os nomes oficiais da API."""

        filtros = self.extrator._normalizar_filtros_recurso(
            "msc_orcamentaria",
            {
                "cod_ibge": 3550308,
                "exercicio": 2024,
                "mes": 12,
                "tipo_matriz": "mscc",
                "classe_conta": 6,
                "tipo_valor": "PERIOD_CHANGE",
            },
        )

        self.assertEqual(
            filtros,
            {
                "id_ente": 3550308,
                "an_referencia": 2024,
                "me_referencia": 12,
                "co_tipo_matriz": "MSCC",
                "classe_conta": 6,
                "id_tv": "period_change",
            },
        )

    def test_rejeita_filtros_obrigatorios_ausentes(self):
        """Recursos com contrato mínimo devem falhar antes de acessar a rede."""

        with self.assertRaises(UserInputError):
            self.extrator._validar_filtros_recurso(
                "extrato_entregas",
                {"id_ente": 3550308},
            )

    def test_rejeita_conflito_entre_alias_e_nome_canonico(self):
        """Mesmo filtro não pode chegar com valores divergentes."""

        with self.assertRaises(UserInputError):
            self.extrator._normalizar_filtros_recurso(
                "extrato_entregas",
                {
                    "exercicio": 2024,
                    "an_referencia": 2025,
                    "id_ente": 3550308,
                },
            )

    def test_rejeita_classe_conta_incompativel(self):
        """Cada família MSC deve aceitar apenas as classes previstas na API."""

        filtros = self.extrator._normalizar_filtros_recurso(
            "msc_orcamentaria",
            {
                "id_ente": 3550308,
                "an_referencia": 2024,
                "me_referencia": 12,
                "co_tipo_matriz": "MSCC",
                "classe_conta": 8,
                "id_tv": "period_change",
            },
        )

        with self.assertRaises(UserInputError):
            self.extrator._validar_filtros_recurso("msc_orcamentaria", filtros)


if __name__ == "__main__":
    unittest.main()
