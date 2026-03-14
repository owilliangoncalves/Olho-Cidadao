"""Testes de contratos do Portal da Transparência."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extracao.portal.base import ExtratorPortalBase
from extracao.portal.fornecedores import ConstrutorDimFornecedoresPortal
from infra.errors import UserInputError
from pipeline_portal import PipelinePortalTransparencia


class _ExtratorPortalConcreto(ExtratorPortalBase):
    """Implementação mínima para validar contratos da classe base."""

    def executar(self):
        """Implementação concreta exigida pela base abstrata."""


class PortalTestCase(unittest.TestCase):
    """Valida contratos críticos do pipeline e da base do Portal."""

    def test_base_rejeita_ausencia_da_chave_da_api_com_erro_de_uso(self):
        """Falta de chave do Portal deve falhar sem traceback genérico."""

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(UserInputError):
                _ExtratorPortalConcreto("/api-de-dados/ceis")

    def test_pipeline_portal_rejeita_intervalo_anual_invalido(self):
        """O pipeline do Portal deve validar o intervalo antes de rodar."""

        with self.assertRaises(UserInputError):
            PipelinePortalTransparencia(ano_inicio=2025, ano_fim=2025)

    def test_pipeline_portal_rejeita_fases_invalidas(self):
        """A etapa de documentos exige ao menos uma fase válida."""

        with patch(
            "pipeline_portal.obter_parametros_pipeline",
            return_value={"min_ocorrencias": 1, "fases": []},
        ):
            pipeline = PipelinePortalTransparencia()

        with self.assertRaises(UserInputError):
            pipeline.executar_documentos()

    def test_construtor_de_fornecedores_usa_config_do_extrator(self):
        """A dimensão não deve depender de defaults da CLI para funcionar."""

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fornecedores.jsonl"
            builder = ConstrutorDimFornecedoresPortal(output_path=str(output_path))

            registros = [
                {
                    "documento": "12.345.678/0001-90",
                    "nome": "Fornecedor A",
                    "ano": "2024",
                    "origem": "camara",
                },
                {
                    "documento": "12.345.678/0001-90",
                    "nome": "Fornecedor A",
                    "ano": "2025",
                    "origem": "senado",
                },
                {
                    "documento": "98.765.432/0001-00",
                    "nome": "Fornecedor B",
                    "ano": "2025",
                    "origem": "senado",
                },
            ]

            with patch(
                "extracao.portal.fornecedores.obter_parametros_extrator",
                return_value={"min_ocorrencias": 2},
            ):
                with patch.object(builder, "_iterar_registros", return_value=iter(registros)):
                    builder.construir()

            conteudo = [json.loads(linha) for linha in output_path.read_text().splitlines()]
            self.assertEqual(len(conteudo), 1)
            self.assertEqual(conteudo[0]["documento"], "12345678000190")


if __name__ == "__main__":
    unittest.main()
