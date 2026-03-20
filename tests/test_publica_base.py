"""Testes dos helpers modulares da base de APIs publicas."""

from __future__ import annotations

import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from extracao.publica.artefatos import derivar_artefatos_publicos
from extracao.publica.artefatos import output_pronto
from extracao.publica.config import PublicaBaseConfig
from extracao.publica.records import build_record
from extracao.publica.records import coerce_items
from extracao.publica.records import write_jsonl_records


class PublicaBaseHelpersTestCase(unittest.TestCase):
    """Valida a separacao modular da base de APIs publicas."""

    def test_publica_base_config_carrega_defaults_e_overrides(self):
        """A config deve consolidar defaults do projeto com overrides locais."""

        with patch(
            "extracao.publica.config.obter_parametros_extrator",
            return_value={
                "rate_limit_per_sec": 1.0,
                "max_rate_per_sec": 3.5,
            },
        ):
            cfg = PublicaBaseConfig.carregar(
                rate_limit_per_sec=2.0,
                max_rate_per_sec=None,
            )

        self.assertEqual(cfg.rate_limit_per_sec, 2.0)
        self.assertEqual(cfg.max_rate_per_sec, 3.5)

    def test_coerce_items_aceita_lista_direta_ou_chaves_conhecidas(self):
        """A normalizacao deve suportar lista crua e envelopes comuns."""

        self.assertEqual(coerce_items([{"id": 1}]), [{"id": 1}])
        self.assertEqual(coerce_items({"results": [{"id": 2}]}), [{"id": 2}])
        self.assertEqual(coerce_items({"erro": True}), [])

    def test_build_record_monta_envelope_padrao(self):
        """O helper de envelope deve preencher `_meta` com rastreabilidade minima."""

        registro = build_record(
            {"id": 10},
            context={"dataset": "regioes"},
            endpoint="/regioes",
            orgao="IBGE",
            nome_endpoint="localidades",
        )

        self.assertEqual(registro["_meta"]["orgao_origem"], "ibge")
        self.assertEqual(registro["_meta"]["nome_endpoint"], "localidades")
        self.assertEqual(registro["_meta"]["dataset"], "regioes")
        self.assertEqual(registro["payload"]["id"], 10)

    def test_write_jsonl_records_serializa_todos_os_itens(self):
        """A escrita modular deve retornar a quantidade persistida."""

        buffer = io.StringIO()
        total = write_jsonl_records(
            buffer,
            [{"id": 1}, {"id": 2}],
            build_record_fn=lambda item: {"payload": item},
        )

        linhas = [json.loads(linha) for linha in buffer.getvalue().splitlines()]
        self.assertEqual(total, 2)
        self.assertEqual(linhas, [{"payload": {"id": 1}}, {"payload": {"id": 2}}])

    def test_derivar_task_artifacts_padroniza_estrutura_publica(self):
        """Os artefatos devem manter o layout compartilhado da base publica."""

        artifacts = derivar_artefatos_publicos(Path("ibge/localidades/regioes.json"))

        self.assertEqual(artifacts.output_path, Path("data/ibge/localidades/regioes.json"))
        self.assertEqual(
            artifacts.state_path,
            Path("data/_estado/publica/ibge/localidades/regioes.state.json"),
        )
        self.assertEqual(artifacts.tmp_path, Path("data/ibge/localidades/regioes.json.tmp"))
        self.assertEqual(artifacts.empty_path, Path("data/ibge/localidades/regioes.json.empty"))

    def test_output_pronto_valida_meta_minimo(self):
        """A validacao da saida pronta deve olhar para `_meta` do primeiro registro."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            caminho = base / "saida.jsonl"
            original_cwd = Path.cwd()

            try:
                os.chdir(base)
                with open(caminho, "w", encoding="utf-8") as arquivo:
                    json.dump(
                        {
                            "_meta": {
                                "orgao_origem": "ibge",
                                "nome_endpoint": "localidades",
                                "endpoint": "/regioes",
                                "dataset": "regioes",
                            },
                            "payload": {"id": 1},
                        },
                        arquivo,
                    )
                    arquivo.write("\n")

                pronto = output_pronto(
                    caminho,
                    required_meta_keys={"orgao_origem", "nome_endpoint", "endpoint"},
                    extra_meta_keys={"dataset"},
                )
            finally:
                os.chdir(original_cwd)

        self.assertTrue(pronto)


if __name__ == "__main__":
    unittest.main()
