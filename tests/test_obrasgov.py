"""Testes do extrator do ObrasGov."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extracao.obrasgov import ObrasGov
from extracao.obrasgov.config import ObrasGovConfig
from extracao.obrasgov.projetos import iterar_ids_projetos
from extracao.obrasgov.projetos import slug_id
from extracao.obrasgov.tarefas import resolver_recursos_paginados


class ExtratorObrasGovTestCase(unittest.TestCase):
    """Valida contratos básicos do extrator do ObrasGov."""

    def test_config_carrega_overrides_e_defaults(self):
        """A configuracao deve centralizar defaults e overrides do extrator."""

        with patch(
            "extracao.obrasgov.config.obter_parametros_extrator",
            return_value={
                "page_size": 500,
                "max_workers": 3,
                "rate_limit_per_sec": 1.0,
                "max_rate_per_sec": 2.5,
            },
        ):
            cfg = ObrasGovConfig.carregar(page_size=200)

        self.assertEqual(cfg.page_size, 200)
        self.assertEqual(cfg.max_workers, 3)
        self.assertEqual(cfg.max_pending, 12)
        self.assertEqual(cfg.rate_limit_per_sec, 1.0)
        self.assertEqual(cfg.max_rate_per_sec, 2.5)

    def test_slug_id_normaliza_para_nome_de_arquivo(self):
        """IDs com caracteres especiais devem produzir nomes seguros."""

        self.assertEqual(slug_id("obra/123?abc"), "obra-123-abc")

    def test_extrator_pode_ser_instanciado(self):
        """A classe concreta deve implementar a interface da base abstrata."""

        extrator = ObrasGov()

        self.assertIsInstance(extrator, ObrasGov)

    def test_executar_delega_para_executar_recursos(self):
        """O método público `executar` deve manter compatibilidade com a base."""

        extrator = ObrasGov()

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

                ids = list(iterar_ids_projetos())
            finally:
                os.chdir(cwd_original)

        self.assertEqual(set(ids), {"FINAL-1", "TMP-1"})

    def test_iterar_ids_projetos_helper_deduplica_ids(self):
        """O helper modular deve deduplicar `idUnico` ao varrer os arquivos."""

        with tempfile.TemporaryDirectory() as tempdir:
            base = Path(tempdir) / "data/obrasgov/projeto-investimento"
            base.mkdir(parents=True, exist_ok=True)
            caminho = base / "consulta=all.json"

            with open(caminho, "w", encoding="utf-8") as arquivo:
                json.dump({"payload": {"idUnico": "OBRA-1"}}, arquivo)
                arquivo.write("\n")
                json.dump({"payload": {"idUnico": "OBRA-1"}}, arquivo)
                arquivo.write("\n")
                json.dump({"payload": {"idUnico": "OBRA-2"}}, arquivo)
                arquivo.write("\n")

            ids = list(iterar_ids_projetos(base_dir=base))

        self.assertEqual(ids, ["OBRA-1", "OBRA-2"])

    def test_resolver_recursos_paginados_separa_validos_e_invalidos(self):
        """Recursos inválidos não devem contaminar a fila válida."""

        validos, invalidos = resolver_recursos_paginados(
            ["execucao-fisica", "bairro", "execucao-fisica", "foo"]
        )

        self.assertEqual(validos, ("execucao-fisica",))
        self.assertEqual(invalidos, ("bairro", "foo"))

    def test_executar_geometrias_usa_cfg_para_limites(self):
        """A orquestracao de geometrias deve respeitar a configuracao carregada."""

        extrator = ObrasGov()
        extrator.cfg = extrator.cfg.__class__(
            page_size=extrator.cfg.page_size,
            max_workers=7,
            rate_limit_per_sec=extrator.cfg.rate_limit_per_sec,
            max_rate_per_sec=extrator.cfg.max_rate_per_sec,
        )

        with (
            patch("extracao.obrasgov.iterar_ids_projetos", return_value=iter(["A", "B"])),
            patch("extracao.obrasgov.executar_tarefas_limitadas") as mock_executor,
        ):
            extrator.executar_geometrias()

        ids = list(mock_executor.call_args.args[0])
        self.assertEqual(ids, ["A", "B"])
        self.assertEqual(mock_executor.call_args.kwargs["max_workers"], 7)
        self.assertEqual(mock_executor.call_args.kwargs["max_pending"], 28)

    def test_executar_recursos_ignora_invalidos_e_processa_validos(self):
        """Recursos inválidos não devem bloquear os válidos restantes."""

        extrator = ObrasGov()

        with patch.object(
            extrator,
            "_executar_tarefa_paginada",
            return_value={"status": "success", "records": 10},
        ) as executar:
            resultados = extrator.executar_recursos(
                recursos=["foo", "execucao-fisica", "foo"],
                filtros={"uf": "SP"},
            )

        self.assertEqual(tuple(resultados), ("execucao-fisica",))
        self.assertEqual(executar.call_count, 1)
        self.assertEqual(executar.call_args.kwargs["endpoint"], "/execucao-fisica")


if __name__ == "__main__":
    unittest.main()
