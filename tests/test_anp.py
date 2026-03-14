"""Testes do extrator de revendedores da ANP."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from extracao.anp.revendedores import ExtratorRevendedoresANP
from extracao.publica.base import ExtratorAPIPublicaBase


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

    def test_nao_reprocessa_consultas_vazias_na_anp(self):
        """Respostas vazias da ANP não devem disparar retry adicional."""

        extrator = ExtratorRevendedoresANP()

        with patch.object(
            extrator,
            "_executar_tarefa_paginada",
            return_value={"status": "empty", "records": 0, "pages": 0},
        ) as mock_executar:
            extrator._executar_tarefa("combustivel", "12345678000190")

        self.assertFalse(mock_executar.call_args.kwargs["_allow_empty_retry"])
        self.assertFalse(mock_executar.call_args.kwargs["_persist_empty_marker"])

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
