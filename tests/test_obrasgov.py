"""Testes do extrator do ObrasGov."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extracao.obrasgov.obras import ExtratorObrasGov


class ExtratorObrasGovTestCase(unittest.TestCase):
    """Valida contratos básicos do extrator do ObrasGov."""

    def test_extrator_pode_ser_instanciado(self):
        """A classe concreta deve implementar a interface da base abstrata."""

        extrator = ExtratorObrasGov()

        self.assertIsInstance(extrator, ExtratorObrasGov)

    def test_executar_delega_para_executar_recursos(self):
        """O método público `executar` deve manter compatibilidade com a base."""

        extrator = ExtratorObrasGov()

        with patch.object(extrator, "executar_recursos") as mock_executar_recursos:
            filtros = {"uf": "SP"}
            recursos = ["projeto-investimento"]

            extrator.executar(recursos=recursos, filtros=filtros)

        mock_executar_recursos.assert_called_once_with(
            recursos=recursos,
            filtros=filtros,
        )

    def test_iterar_ids_projetos_considera_tmp_sem_arquivo_final(self):
        """As geometrias devem aproveitar projetos já persistidos em `.json.tmp`."""

        extrator = ExtratorObrasGov()

        with tempfile.TemporaryDirectory() as tempdir:
            cwd_original = os.getcwd()
            os.chdir(tempdir)
            try:
                base = Path("data/obrasgov/projeto-investimento")
                base.mkdir(parents=True, exist_ok=True)

                final_path = base / "consulta=parcial.json"
                tmp_path = base / "consulta=all.json.tmp"

                with open(final_path, "w", encoding="utf-8") as arquivo:
                    json.dump({"payload": {"idUnico": "FINAL-1"}}, arquivo)
                    arquivo.write("\n")

                with open(tmp_path, "w", encoding="utf-8") as arquivo:
                    json.dump({"payload": {"idUnico": "TMP-1"}}, arquivo)
                    arquivo.write("\n")
                    json.dump({"payload": {"idUnico": "FINAL-1"}}, arquivo)
                    arquivo.write("\n")

                ids = list(extrator._iterar_ids_projetos())
            finally:
                os.chdir(cwd_original)

        self.assertEqual(set(ids), {"FINAL-1", "TMP-1"})


if __name__ == "__main__":
    unittest.main()
