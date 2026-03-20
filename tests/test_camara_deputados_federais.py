"""Testes do pacote de deputados federais da Câmara."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from configuracao import obter_configuracao_endpoint
from extracao.camara.deputados_federais import Despesas
from extracao.camara.deputados_federais.dados import iterar_ids_legislaturas
from extracao.camara.deputados_federais.dados import iterar_trabalhos_despesas


class DadosCamaraHelpersTestCase(unittest.TestCase):
    """Valida helpers puros usados pela orquestração da Câmara."""

    def test_iterar_ids_legislaturas_ignora_linhas_invalidas(self):
        """A leitura do arquivo mestre deve devolver apenas IDs válidos."""

        with TemporaryDirectory() as tmpdir:
            caminho = Path(tmpdir) / "legislaturas.json"
            caminho.write_text(
                '\n'.join(
                    [
                        json.dumps({"id": 57}),
                        "invalido",
                        "",
                        json.dumps({"sem_id": 1}),
                        json.dumps({"id": 58}),
                    ]
                ),
                encoding="utf-8",
            )

            ids = list(iterar_ids_legislaturas(caminho))

        self.assertEqual(ids, [57, 58])

    def test_iterar_trabalhos_despesas_deduplica_e_prioriza_mais_recente(self):
        """Deputado/ano não deve ser repetido e arquivos novos entram primeiro."""

        with TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            pasta = base / "deputados_por_legislaturas"
            pasta.mkdir()
            (pasta / "deputados_legislaturas_57.json").write_text(
                json.dumps(
                    {
                        "id": 100,
                        "idLegislatura": 57,
                        "nome": "Antigo",
                        "siglaUf": "SP",
                        "siglaPartido": "AAA",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (pasta / "deputados_legislaturas_58.json").write_text(
                json.dumps(
                    {
                        "id": 100,
                        "idLegislatura": 58,
                        "nome": "Recente",
                        "siglaUf": "RJ",
                        "siglaPartido": "BBB",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            trabalhos = list(
                iterar_trabalhos_despesas(
                    pasta,
                    "id",
                    {
                        57: (date(2023, 1, 1), date(2023, 12, 31)),
                        58: (date(2024, 2, 1), date(2025, 1, 31)),
                    },
                    date(2023, 1, 1),
                    date(2025, 12, 31),
                )
            )

        self.assertEqual(
            trabalhos,
            [
                ("100", 2025, {"id_legislatura": 58, "nome": "Recente", "sigla_uf": "RJ", "sigla_partido": "BBB", "uri": None}),
                ("100", 2024, {"id_legislatura": 58, "nome": "Recente", "sigla_uf": "RJ", "sigla_partido": "BBB", "uri": None}),
                ("100", 2023, {"id_legislatura": 57, "nome": "Antigo", "sigla_uf": "SP", "sigla_partido": "AAA", "uri": None}),
            ],
        )


class DespesasCamaraTestCase(unittest.TestCase):
    """Valida a orquestração das despesas por deputado."""

    def _novo_extrator(self, pasta_dados: str) -> Despesas:
        return Despesas(
            "deputados_despesas",
            obter_configuracao_endpoint("deputados_despesas"),
            pasta_dados=pasta_dados,
        )

    def test_executar_tarefa_mapeia_status_para_checkpoint_e_stats(self):
        """Cada resumo do extrator interno deve atualizar checkpoint e contadores."""

        casos = [
            (
                {"status": "success", "records": 9, "pages": 2},
                "completed",
                "mark_success",
                {"records": 9, "pages": 2},
            ),
            (
                {"status": "empty", "records": 0, "pages": 3},
                "empty",
                "mark_empty",
                {"pages": 3},
            ),
            (
                {"status": "skipped_empty", "records": 0, "pages": 0},
                "skipped",
                "mark_empty",
                {"pages": 0},
            ),
            (
                {"status": "skipped", "records": 0, "pages": 0},
                "skipped",
                "mark_success",
                {"records": -1, "pages": 0, "message": "arquivo final reutilizado"},
            ),
        ]

        for resumo, contador, metodo_checkpoint, extras in casos:
            with self.subTest(status=resumo["status"]):
                with TemporaryDirectory() as tmpdir:
                    extrator = self._novo_extrator(tmpdir)
                    extrator.checkpoints = MagicMock()
                    extrator.checkpoints.is_terminal.return_value = False
                    extrator.checkpoints.get_status.return_value = None

                    with patch(
                        "extracao.camara.deputados_federais._ExtratorDespesaDeputado"
                    ) as interno_cls:
                        interno_cls.return_value.executar.return_value = resumo
                        extrator._executar_tarefa(
                            "123",
                            2024,
                            {"id_legislatura": 57, "nome": "Deputado"},
                        )

                self.assertEqual(extrator.stats.snapshot()[contador], 1)
                getattr(extrator.checkpoints, metodo_checkpoint).assert_called_once()
                chamada = getattr(extrator.checkpoints, metodo_checkpoint).call_args.kwargs
                self.assertEqual(chamada["endpoint"], "deputados_despesas")
                self.assertEqual(chamada["entity_id"], "123")
                self.assertEqual(chamada["context"], "2024")
                for chave, valor in extras.items():
                    self.assertEqual(chamada[chave], valor)


if __name__ == "__main__":
    unittest.main()
