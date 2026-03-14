"""Testes para helpers de inspeção leve de JSON Lines."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.jsonl import arquivo_jsonl_meta_tem_chaves


class JsonlHelpersTestCase(unittest.TestCase):
    """Garante contratos simples dos utilitários de leitura leve."""

    def test_arquivo_jsonl_meta_tem_chaves_valida_meta_do_primeiro_registro(self):
        """As chaves requeridas devem ser encontradas dentro de `_meta`."""

        with TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "dados.json"
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"_meta": {"dataset": "demo", "orgao_origem": "teste"}}, f)
                f.write("\n")

            self.assertTrue(
                arquivo_jsonl_meta_tem_chaves(
                    caminho,
                    {"dataset", "orgao_origem"},
                )
            )
            self.assertFalse(
                arquivo_jsonl_meta_tem_chaves(
                    caminho,
                    {"dataset", "nome_endpoint"},
                )
            )


if __name__ == "__main__":
    unittest.main()
