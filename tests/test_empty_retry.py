"""Testes para a revalidação automática de marcadores `.empty`."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from extracao.publica import ExtratorAPIPublicaBase


class _ExtratorPublicoFalso(ExtratorAPIPublicaBase):
    """Stub mínimo para validar a política de retry de `.empty`."""

    def __init__(self, respostas):
        super().__init__(orgao="ibge", nome_endpoint="localidades")
        self.respostas = list(respostas)

    def _request_publica(self, endpoint: str, params: dict | None = None, timeout=(15, 120)):
        """Retorna respostas predefinidas sem acessar a rede."""

        if not self.respostas:
            return []
        return self.respostas.pop(0)

    def executar(self):
        """Não é usado nestes testes."""


class EmptyRetryTestCase(unittest.TestCase):
    """Exercita o retry único de tarefas marcadas como vazias."""

    def test_tarefa_unica_reprocessa_empty_existente_uma_vez(self):
        """Um `.empty` herdado deve ser reavaliado e virar sucesso com dados."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            extrator = _ExtratorPublicoFalso([[{"id": 1, "nome": "SP"}]])
            original_cwd = Path.cwd()

            try:
                os.chdir(base)
                empty = base / "data/ibge/localidades/regioes.json.empty"
                empty.parent.mkdir(parents=True, exist_ok=True)
                empty.touch()

                resumo = extrator._executar_tarefa_unica(
                    endpoint="/regioes",
                    params={},
                    relative_output_path=Path("ibge/localidades/regioes.json"),
                    context={"dataset": "regioes"},
                )

                self.assertEqual(resumo["status"], "success")
                self.assertFalse(empty.exists())
                self.assertTrue((base / "data/ibge/localidades/regioes.json").exists())
            finally:
                os.chdir(original_cwd)

    def test_tarefa_unica_remove_empty_apos_retentativa_vazia(self):
        """Depois da revalidação, o `.empty` não deve mais permanecer em disco."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            extrator = _ExtratorPublicoFalso([[], []])
            original_cwd = Path.cwd()

            try:
                os.chdir(base)

                resumo = extrator._executar_tarefa_unica(
                    endpoint="/regioes",
                    params={},
                    relative_output_path=Path("ibge/localidades/regioes.json"),
                    context={"dataset": "regioes"},
                )

                self.assertEqual(resumo["status"], "empty")
                self.assertFalse((base / "data/ibge/localidades/regioes.json.empty").exists())
                self.assertFalse((base / "data/ibge/localidades/regioes.json").exists())
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
