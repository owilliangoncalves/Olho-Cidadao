"""Testes do endurecimento de parâmetros do extrator Siconfi."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from extracao.siconfi import preparar_consultas_siconfi
from extracao.siconfi import Siconfi
from extracao.siconfi import SICONFI_RESOURCES
from extracao.siconfi.filtros import normalizar_filtros_recurso
from extracao.siconfi.filtros import obter_spec_siconfi
from extracao.siconfi.filtros import validar_filtros_recurso
from extracao.siconfi.tarefas import resolver_recursos_siconfi
from infra.errors import UserInputError


class SiconfiValidationTestCase(unittest.TestCase):
    """Valida normalização e contrato mínimo de filtros do Siconfi."""

    def setUp(self):
        """Cria uma instância reutilizável do extrator sob teste."""

        self.extrator = Siconfi()

    def test_reexporta_recursos_suportados(self):
        """O mapa público de recursos deve permanecer acessível pela API."""

        self.assertIn("entes", SICONFI_RESOURCES)
        self.assertIn("rgf", SICONFI_RESOURCES)

    def test_resolver_recursos_siconfi_remove_duplicatas(self):
        """A seleção de recursos deve preservar ordem sem repetir itens."""

        self.assertEqual(
            resolver_recursos_siconfi(["entes", "rgf", "entes"]),
            ("entes", "rgf"),
        )

    def test_preparar_consultas_siconfi_normaliza_e_valida(self):
        """A preparação leve deve produzir a consulta pronta antes do extrator."""

        consultas = preparar_consultas_siconfi(
            ["extrato_entregas"],
            {"cod_ibge": 3550308, "exercicio": 2024},
        )

        self.assertEqual(len(consultas), 1)
        recurso, spec, filtros = consultas[0]
        self.assertEqual(recurso, "extrato_entregas")
        self.assertEqual(spec.path, "/extrato_entregas")
        self.assertEqual(filtros, {"id_ente": 3550308, "an_referencia": 2024})

    def test_obter_spec_siconfi_rejeita_recurso_desconhecido(self):
        """Recursos fora do catálogo devem falhar com erro de entrada."""

        with self.assertRaises(UserInputError):
            obter_spec_siconfi("foo")

    def test_normaliza_aliases_de_msc_orcamentaria(self):
        """Aliases comuns devem ser convertidos para os nomes oficiais da API."""

        filtros = normalizar_filtros_recurso(
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
            validar_filtros_recurso(
                "extrato_entregas",
                {"id_ente": 3550308},
            )

    def test_rejeita_conflito_entre_alias_e_nome_canonico(self):
        """Mesmo filtro não pode chegar com valores divergentes."""

        with self.assertRaises(UserInputError):
            normalizar_filtros_recurso(
                "extrato_entregas",
                {
                    "exercicio": 2024,
                    "an_referencia": 2025,
                    "id_ente": 3550308,
                },
            )

    def test_rejeita_classe_conta_incompativel(self):
        """Cada família MSC deve aceitar apenas as classes previstas na API."""

        filtros = normalizar_filtros_recurso(
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
            validar_filtros_recurso("msc_orcamentaria", filtros)

    def test_executar_delega_para_tarefa_paginada_com_filtros_normalizados(self):
        """O extrator deve montar a tarefa final a partir da lógica modular."""

        with patch.object(
            self.extrator,
            "_executar_tarefa_paginada",
            return_value={"status": "success", "records": 1, "pages": 1},
        ) as mock_executar:
            self.extrator.executar(
                recursos=["extrato_entregas"],
                filtros={"cod_ibge": 3550308, "exercicio": 2024},
            )

        kwargs = mock_executar.call_args.kwargs
        self.assertEqual(kwargs["endpoint"], "/extrato_entregas")
        self.assertEqual(
            kwargs["base_params"],
            {"id_ente": 3550308, "an_referencia": 2024},
        )
        self.assertEqual(kwargs["context"]["dataset"], "extrato_entregas")
        self.assertEqual(kwargs["context"]["filtros"]["id_ente"], 3550308)


if __name__ == "__main__":
    unittest.main()
