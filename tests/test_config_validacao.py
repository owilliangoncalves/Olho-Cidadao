"""Testes de compatibilidade do schema tipado de configuracao."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from configuracao.validacao import construir_config_projeto


class ConfigValidacaoTestCase(unittest.TestCase):
    """Garante compatibilidade entre o schema tipado e o TOML real do projeto."""

    def test_etl_config_toml_construi_schema_tipado_sem_campos_desconhecidos(self):
        """O arquivo de config real deve ser aceito pela validacao tipada."""

        caminho = Path("etl-config.toml")
        with open(caminho, "rb") as arquivo:
            raw = tomllib.load(arquivo)

        config = construir_config_projeto(raw)

        self.assertEqual(config.endpoints["legislaturas"].salvar_como, "legislaturas.json")
        self.assertTrue(config.endpoints["legislaturas"].paginacao)
        self.assertEqual(config.endpoints["ceaps"].ano_inicio, 2008)
        self.assertEqual(config.endpoints["ceaps"].ano_fim, 2026)
        self.assertTrue(config.endpoints["portal_documentos_favorecido"].restricted)
        self.assertEqual(config.endpoints["portal_documentos_favorecido"].fases, [1, 2, 3])
        self.assertEqual(config.pipelines["completo"].ano_inicio, 2012)
        self.assertEqual(config.pipelines["completo"].ano_fim, 2026)
        self.assertEqual(config.pipelines["completo"].max_workers, 4)
        self.assertTrue(config.pipelines["completo"].fontes["camara"])
        self.assertEqual(config.pipelines["completo"].senado["endpoint"], "ceaps")


if __name__ == "__main__":
    unittest.main()
