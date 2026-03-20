"""Testes do pacote de localidades do IBGE."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from extracao.ibge import IBGE_DATASETS
from extracao.ibge import LocalidadesIBGE
from extracao.ibge.tarefas import output_path_localidade
from extracao.ibge.tarefas import resolver_datasets_solicitados


class IbgeHelpersTestCase(unittest.TestCase):
    """Valida helpers puros usados pelo pacote do IBGE."""

    def test_resolver_datasets_solicitados_separa_validos_e_invalidos(self):
        """Datasets desconhecidos não devem contaminar a fila válida."""

        validos, invalidos = resolver_datasets_solicitados(
            ["municipios", "bairro", "estados", "municipios", "bairro"]
        )

        self.assertEqual(validos, ("municipios", "estados"))
        self.assertEqual(invalidos, ("bairro",))

    def test_output_path_localidade_monta_saida_padrao(self):
        """O caminho relativo de saída deve seguir a convenção do pacote."""

        self.assertEqual(
            output_path_localidade("regioes").as_posix(),
            "ibge/localidades/regioes.json",
        )


class LocalidadesIBGETestCase(unittest.TestCase):
    """Valida a orquestração pública do extrator IBGE."""

    def test_executar_ignora_invalidos_e_processa_validos(self):
        """O orquestrador deve seguir com os datasets válidos restantes."""

        extrator = LocalidadesIBGE()
        with patch.object(
            extrator,
            "_executar_tarefa_unica",
            return_value={"status": "success", "records": 27},
        ) as executar:
            resultados = extrator.executar(["bairro", "estados", "regioes"])

        self.assertEqual(tuple(resultados), ("estados", "regioes"))
        self.assertEqual(executar.call_count, 2)
        self.assertEqual(executar.call_args_list[0].kwargs["endpoint"], IBGE_DATASETS["estados"])
        self.assertEqual(
            executar.call_args_list[0].kwargs["relative_output_path"].as_posix(),
            "ibge/localidades/estados.json",
        )

    def test_executar_retorna_vazio_quando_nao_ha_dataset_valido(self):
        """Quando tudo é inválido, o pacote deve encerrar sem chamadas HTTP."""

        extrator = LocalidadesIBGE()
        with patch.object(extrator, "_executar_tarefa_unica") as executar:
            resultados = extrator.executar(["bairro"])

        self.assertEqual(resultados, {})
        executar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
