"""Testes da fachada publica e dos shims de compatibilidade de configuracao."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import configuracao
from configuracao.modelos import ConfigOperacional
from configuracao.modelos import EndpointConfig
from configuracao.modelos import PipelineConfig
from configuracao.modelos import ProjetoConfig


class ConfiguracaoPublicaTestCase(unittest.TestCase):
    """Valida a fachada consolidada em `configuracao.__init__`."""

    def _fake_config(self) -> ProjetoConfig:
        return ProjetoConfig(
            endpoints={
                "ceaps": EndpointConfig(
                    endpoint="https://dados.senado.leg.br/ceaps",
                    itens=100,
                    campo_id="codigo",
                    paginacao=True,
                )
            },
            pipelines={
                "portal": PipelineConfig(
                    etapas=["dimensao", "documentos"],
                    max_workers=4,
                    fontes={"portal": True},
                )
            },
            config=ConfigOperacional(
                cli={
                    "meu_comando": {"ativo": True},
                    "intervalo_anos": {"ano_inicio": 2020, "ano_fim": 2024},
                },
                extratores={"portal_api": {"rate_limit_per_sec": 1.5}},
                pipelines={"pipeline_x": {"max_workers": 8}},
            ),
        )

    def test_fachada_publica_expande_api_essencial_do_pacote(self):
        """O pacote deve expor o conjunto principal de acessores e modelos."""

        for nome in (
            "PROJECT_ROOT",
            "CONFIG_PATH",
            "obter_config",
            "obter_configuracao",
            "obter_configuracao_endpoint",
            "obter_configuracao_pipeline",
            "obter_parametros_cli",
            "obter_parametros_extrator",
            "obter_parametros_pipeline",
            "resolver_data_configurada",
            "resolver_data_configurada_iso",
            "urls",
        ):
            self.assertTrue(hasattr(configuracao, nome), nome)

    def test_obter_configuracao_endpoint_exporta_dataclass_como_dict(self):
        """Endpoints tipados devem sair como dict sem expor a dataclass."""

        with patch(
            "configuracao.acesso.carregar_configuracao_tipada",
            return_value=self._fake_config(),
        ):
            config = configuracao.obter_configuracao_endpoint("ceaps")

        self.assertEqual(config["endpoint"], "https://dados.senado.leg.br/ceaps")
        self.assertEqual(config["itens"], 100)
        self.assertEqual(config["campo_id"], "codigo")
        self.assertTrue(config["paginacao"])

    def test_obter_configuracao_pipeline_exporta_dict_tipado(self):
        """Pipelines tipados devem sair como dict para consumo operacional."""

        with patch(
            "configuracao.acesso.carregar_configuracao_tipada",
            return_value=self._fake_config(),
        ):
            config = configuracao.obter_configuracao_pipeline("portal")

        self.assertEqual(config["etapas"], ["dimensao", "documentos"])
        self.assertEqual(config["max_workers"], 4)
        self.assertTrue(config["fontes"]["portal"])

    def test_obter_parametros_normaliza_hifens_e_retorna_copia(self):
        """Acesso operacional deve resolver nomes com hífen sem vazar referência."""

        bruto = {
            "config": {
                "cli": {"meu_comando": {"ativo": True}},
                "extratores": {"portal_api": {"rate_limit_per_sec": 1.5}},
                "pipelines": {"pipeline_x": {"max_workers": 8}},
            }
        }

        with patch("configuracao.acesso.carregar_configuracao_bruta", return_value=bruto):
            cli_cfg = configuracao.obter_parametros_cli("meu-comando")
            extrator_cfg = configuracao.obter_parametros_extrator("portal-api")
            pipeline_cfg = configuracao.obter_parametros_pipeline("pipeline-x")

        cli_cfg["ativo"] = False

        self.assertEqual(extrator_cfg["rate_limit_per_sec"], 1.5)
        self.assertEqual(pipeline_cfg["max_workers"], 8)
        self.assertTrue(bruto["config"]["cli"]["meu_comando"]["ativo"])

    def test_obter_configuracao_retorna_default_profundo_quando_caminho_ausente(self):
        """Defaults mutáveis não devem vazar referência compartilhada."""

        with patch("configuracao.acesso.carregar_configuracao_bruta", return_value={}):
            valor = configuracao.obter_configuracao("config.inexistente", default={"ok": []})
            referencia = configuracao.obter_configuracao(
                "config.inexistente",
                default={"ok": []},
            )

        valor["ok"].append("x")
        self.assertEqual(referencia, {"ok": []})

    def test_urls_publico_continua_disponivel_no_pacote(self):
        """`urls` deve seguir disponível diretamente na fachada do pacote."""

        self.assertIsInstance(configuracao.urls, dict)


if __name__ == "__main__":
    unittest.main()
