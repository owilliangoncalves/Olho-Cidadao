"""Testes do extrator de CEAPS do Senado."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from extracao.senado import DadosSenado
from extracao.senado.arquivos import artefatos_ano_senado
from extracao.senado.arquivos import estado_inicial_senado
from extracao.senado.config import SenadoConfig
from extracao.senado.dados import enriquecer_registro_senado
from extracao.senado.dados import iterar_despesas_senado
from extracao.senado.persistencia import salvar_despesas_ano
from extracao.senado.tarefas import contador_por_status
from extracao.senado.tarefas import iterar_anos_senado


class ExtratorSenadoTestCase(unittest.TestCase):
    """Valida a modularizacao e os contratos basicos do extrator do Senado."""

    def _extrator(self) -> DadosSenado:
        with patch(
            "extracao.senado.config.obter_configuracao_endpoint",
            return_value={
                "endpoint": "/ceaps/{ano}",
                "ano_inicio": 2023,
                "ano_fim": 2024,
            },
        ):
            return DadosSenado("ceaps")

    def test_senado_config_carrega_endpoint_e_intervalo(self):
        """A configuracao deve ser resolvida a partir do catalogo de endpoints."""

        with patch(
            "extracao.senado.config.obter_configuracao_endpoint",
            return_value={
                "endpoint": "/ceaps/{ano}",
                "ano_inicio": 2023,
                "ano_fim": 2024,
            },
        ):
            cfg = SenadoConfig.carregar("ceaps")

        self.assertEqual(cfg.nome_endpoint, "ceaps")
        self.assertEqual(cfg.endpoint, "/ceaps/{ano}")
        self.assertEqual(cfg.ano_inicio, 2023)
        self.assertEqual(cfg.ano_fim, 2024)

    def test_iterar_despesas_senado_aceita_dict_lista_ou_item_unico(self):
        """O parser deve normalizar os formatos conhecidos da resposta do Senado."""

        lista = list(
            iterar_despesas_senado(
                {"ListaDespesas": {"Despesas": [{"id": 1}, {"id": 2}]}}
            )
        )
        item_unico = list(iterar_despesas_senado({"ListaDespesas": {"Despesas": {"id": 3}}}))

        self.assertEqual(lista, [{"id": 1}, {"id": 2}])
        self.assertEqual(item_unico, [{"id": 3}])

    def test_enriquecer_registro_senado_adiciona_chaves_derivadas_sem_mutar_entrada(self):
        """O enriquecimento deve preservar o item original e adicionar o schema esperado."""

        original = {"cpfCnpj": "12.345.678/0001-90", "valor": 10}
        enriquecido = enriquecer_registro_senado(original, ano=2024, nome_endpoint="ceaps")

        self.assertEqual(original, {"cpfCnpj": "12.345.678/0001-90", "valor": 10})
        self.assertEqual(enriquecido["documento_fornecedor_normalizado"], "12345678000190")
        self.assertEqual(enriquecido["tipo_documento_fornecedor"], "cnpj")
        self.assertEqual(enriquecido["cnpj_base_fornecedor"], "12345678")
        self.assertEqual(enriquecido["orgao_origem"], "senado")
        self.assertEqual(enriquecido["endpoint_origem"], "ceaps")
        self.assertEqual(enriquecido["ano_arquivo"], 2024)

    def test_artefatos_ano_derivam_caminhos_e_estado_padrao(self):
        """Os artefatos anuais devem seguir o layout esperado do projeto."""

        arquivos = artefatos_ano_senado(2024)

        self.assertEqual(arquivos.saida, Path("data/senadores/ceaps_2024.json"))
        self.assertEqual(arquivos.temporario, Path("data/senadores/ceaps_2024.json.tmp"))
        self.assertEqual(arquivos.empty, Path("data/senadores/ceaps_2024.json.empty"))
        self.assertEqual(
            arquivos.estado,
            Path("data/_estado/senado/senadores/ceaps_2024.state.json"),
        )
        self.assertEqual(estado_inicial_senado(), {"status": "pending", "attempts": 0, "records": 0})

    def test_salvar_despesas_ano_grava_jsonl_enriquecido(self):
        """A serializacao anual deve promover o temporario com registros enriquecidos."""

        with TemporaryDirectory() as tempdir:
            original_cwd = Path.cwd()
            try:
                os.chdir(tempdir)
                total = salvar_despesas_ano(
                    artefatos_ano_senado(2024),
                    [{"cpfCnpj": "12.345.678/0001-90", "valor": 10}],
                    ano=2024,
                    nome_endpoint="ceaps",
                    logger=self._extrator().logger,
                    orgao="SENADO",
                )

                caminho = Path("data/senadores/ceaps_2024.json")
                with open(caminho, encoding="utf-8") as arquivo:
                    registro = json.loads(arquivo.readline())
            finally:
                os.chdir(original_cwd)

        self.assertEqual(total, 1)
        self.assertEqual(registro["documento_fornecedor_normalizado"], "12345678000190")
        self.assertEqual(registro["orgao_origem"], "senado")
        self.assertEqual(registro["endpoint_origem"], "ceaps")

    def test_tarefas_senado_normalizam_ordem_e_status(self):
        """Os helpers puros devem centralizar ordem anual e contagem final."""

        self.assertEqual(list(iterar_anos_senado(2023, 2024)), [2024, 2023])
        self.assertEqual(contador_por_status("success"), "completed")
        self.assertEqual(contador_por_status("skipped_empty"), "skipped")
        self.assertEqual(contador_por_status("empty"), "empty")
        self.assertEqual(contador_por_status("error"), "failed")


if __name__ == "__main__":
    unittest.main()
