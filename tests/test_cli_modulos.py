"""Testes unitários para a fachada única da CLI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cli
from cli import comun


class CliFacadeTestCase(unittest.TestCase):
    """Valida a fachada pública consolidada em `cli.__init__`."""

    def test_handlers_expoem_aliases_e_apontam_para_mesmo_handler(self):
        """Os aliases de comando devem compartilhar o mesmo handler final."""

        self.assertIs(cli.HANDLERS["menu"], cli.handle_menu)
        self.assertIs(cli.HANDLERS["abrir-menu"], cli.handle_menu)
        self.assertIs(
            cli.HANDLERS["servir-cidadao-de-olho"],
            cli.handle_servir_cidadao_de_olho,
        )
        self.assertIs(
            cli.HANDLERS["abrir-cidadao-de-olho"],
            cli.handle_servir_cidadao_de_olho,
        )

    def test_run_command_despacha_para_handler_registrado(self):
        """O dispatcher central deve repassar o namespace ao handler correto."""

        chamado = []

        def handler_falso(args):
            chamado.append(args.comando)

        args = argparse.Namespace(comando="menu")
        with patch.dict(cli.HANDLERS, {"menu": handler_falso}):
            cli.run_command(args)

        self.assertEqual(chamado, ["menu"])

    def test_main_retorna_codigo_1_para_excecao_inesperada(self):
        """Falhas não tratadas devem encerrar a CLI com código 1."""

        def falhar(_args):
            raise RuntimeError("boom")

        with patch.dict(cli.HANDLERS, {"menu": falhar}):
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["menu"])

        self.assertEqual(ctx.exception.code, 1)

    def test_catalogo_integrado_nao_repete_nomes_de_comandos(self):
        """A orquestração em `cli.__init__` deve manter nomes únicos."""

        nomes = [comando.name for comando in cli.COMMANDS]
        self.assertEqual(len(nomes), len(set(nomes)))
        self.assertEqual(len(nomes), 25)


class CliCommonTestCase(unittest.TestCase):
    """Valida helpers declarativos reutilizados pela CLI."""

    def test_adicionar_flag_inclusao_suporta_tristate(self):
        """Sem flag o valor fica `None`, com override assume bool explícito."""

        parser = argparse.ArgumentParser()
        comun.adicionar_flag_inclusao(
            parser,
            nome="portal",
            destino="incluir_portal",
            descricao="o portal",
        )

        self.assertIsNone(parser.parse_args([]).incluir_portal)
        self.assertTrue(parser.parse_args(["--portal"]).incluir_portal)
        self.assertFalse(parser.parse_args(["--sem-portal"]).incluir_portal)

    def test_helpers_de_argumento_repetivel_e_numerico(self):
        """Os helpers comuns devem padronizar filtros, paginação e limites."""

        parser = argparse.ArgumentParser()
        comun.adicionar_arg_filtros(parser)
        comun.adicionar_arg_tamanho_pagina(parser, default=25)
        comun.adicionar_arg_min_ocorrencias(parser, default=3)
        comun.adicionar_arg_limit_fornecedores(parser)

        args = parser.parse_args(
            [
                "--filtro",
                "ano=2024",
                "--filtro",
                "uf=sp",
                "--tamanho-pagina",
                "99",
                "--min-ocorrencias",
                "7",
                "--limit-fornecedores",
                "12",
            ]
        )

        self.assertEqual(args.filtro, ["ano=2024", "uf=sp"])
        self.assertEqual(args.tamanho_pagina, 99)
        self.assertEqual(args.min_ocorrencias, 7)
        self.assertEqual(args.limit_fornecedores, 12)


class CliParserCoverageTestCase(unittest.TestCase):
    """Cobre o catálogo e o parsing da CLI pública."""

    def test_catalogo_publico_contem_grupos_esperados(self):
        """A fachada deve expor o catálogo consolidado completo."""

        nomes = {comando.name for comando in cli.COMMANDS}

        for esperado in (
            "menu",
            "rodar-pipeline",
            "rodar-paralelo",
            "rodar-pipeline-completo",
            "rodar-pipeline-portal",
            "extrair-senado",
            "extrair-pncp",
            "extrair-obrasgov",
            "extrair-siconfi",
            "extrair-anp",
        ):
            self.assertIn(esperado, nomes)

    def test_parser_configura_comandos_do_portal(self):
        """O parser deve aceitar o conjunto completo de argumentos do Portal."""

        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "extrair-portal-documentos",
                "--min-ocorrencias",
                "4",
                "--limit-fornecedores",
                "20",
                "--ano-inicio",
                "2020",
                "--ano-fim",
                "2023",
                "--fases",
                "1",
                "3",
            ]
        )

        self.assertEqual(args.comando, "extrair-portal-documentos")
        self.assertEqual(args.min_ocorrencias, 4)
        self.assertEqual(args.limit_fornecedores, 20)
        self.assertEqual(args.ano_inicio, 2020)
        self.assertEqual(args.ano_fim, 2023)
        self.assertEqual(args.fases, [1, 3])

    def test_parser_configura_comandos_de_fontes_com_filtros(self):
        """Comandos de fontes complementares devem expor filtros e recursos."""

        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "extrair-transferegov-especial",
                "--recursos",
                "programa_especial",
                "--filtro",
                "uf=sp",
                "--tamanho-pagina",
                "150",
            ]
        )

        self.assertEqual(args.comando, "extrair-transferegov-especial")
        self.assertEqual(args.recursos, ["programa_especial"])
        self.assertEqual(args.filtro, ["uf=sp"])
        self.assertEqual(args.tamanho_pagina, 150)

    def test_parser_configura_anp_e_geometrias(self):
        """Os comandos ANP e ObrasGov geometrias devem aceitar overrides simples."""

        parser = cli.build_parser()
        args_anp = parser.parse_args(
            [
                "extrair-anp",
                "--datasets",
                "combustivel",
                "--min-ocorrencias",
                "5",
                "--limit-fornecedores",
                "9",
            ]
        )
        args_geo = parser.parse_args(["extrair-obrasgov-geometrias", "--limit-ids", "30"])

        self.assertEqual(args_anp.datasets, ["combustivel"])
        self.assertEqual(args_anp.min_ocorrencias, 5)
        self.assertEqual(args_anp.limit_fornecedores, 9)
        self.assertEqual(args_geo.limit_ids, 30)


class CliHandlerWiringTestCase(unittest.TestCase):
    """Valida o wiring dos handlers com seus orquestradores."""

    def test_interface_resolve_caminho_do_binario(self):
        """O helper deve escolher o perfil correto para debug e release."""

        app_dir = Path("/tmp/cidadao")
        self.assertEqual(
            cli._binario_cidadao_de_olho(app_dir, False),
            app_dir / "target" / "debug" / "cidadao_de_olho-cli",
        )
        self.assertEqual(
            cli._binario_cidadao_de_olho(app_dir, True),
            app_dir / "target" / "release" / "cidadao_de_olho-cli",
        )

    def test_interface_verifica_binario_atualizado(self):
        """O helper deve comparar timestamps das fontes com o binário."""

        with TemporaryDirectory() as tmpdir:
            app_dir = Path(tmpdir)
            src_dir = app_dir / "src"
            src_dir.mkdir()
            (app_dir / "Cargo.toml").write_text("cargo", encoding="utf-8")
            (app_dir / "Cargo.lock").write_text("lock", encoding="utf-8")
            (src_dir / "main.rs").write_text("fn main() {}", encoding="utf-8")

            binario = app_dir / "target" / "debug" / "cidadao_de_olho-cli"
            binario.parent.mkdir(parents=True)
            binario.write_text("bin", encoding="utf-8")

            agora = 1_700_000_000
            antigo = agora - 120
            for caminho in (
                app_dir / "Cargo.toml",
                app_dir / "Cargo.lock",
                src_dir / "main.rs",
            ):
                os.utime(caminho, (antigo, antigo))
            os.utime(binario, (agora, agora))

            self.assertTrue(cli._binario_cidadao_de_olho_esta_atualizado(app_dir, binario))

    def test_camara_handle_rodar_pipeline_encadeia_pipeline_camara(self):
        """O handler da Câmara deve instanciar e executar o pipeline correto."""

        args = SimpleNamespace(ano_inicio=2020, ano_fim=2023)
        with patch("pipeline.PipelineCamara") as pipeline_cls:
            cli.handle_rodar_pipeline(args)

        pipeline_cls.assert_called_once_with(ano_inicio=2020, ano_fim=2023)
        pipeline_cls.return_value.executar.assert_called_once_with()

    def test_camara_handle_baixar_legislaturas_usa_pacote_publico(self):
        """O handler deve importar a orquestração pública do pacote da Câmara."""

        with patch("extracao.camara.deputados_federais.Legislatura") as extrator_cls:
            cli.handle_baixar_legislaturas(SimpleNamespace())

        extrator_cls.assert_called_once_with()
        extrator_cls.return_value.executar.assert_called_once_with()

    def test_camara_handle_extrair_legislaturas_usa_pacote_publico(self):
        """A expansão por legislatura deve sair do `__init__` do pacote."""

        with patch("extracao.camara.deputados_federais.DeputadosLegislatura") as extrator_cls:
            cli.handle_extrair_legislaturas(SimpleNamespace())

        extrator_cls.assert_called_once_with()
        extrator_cls.return_value.executar.assert_called_once_with()

    def test_camara_handle_extrair_dependentes_usa_pacote_publico(self):
        """O handler de dependentes deve delegar a orquestração ao pacote."""

        args = SimpleNamespace(endpoint="deputados_despesas", ano_inicio=2023, ano_fim=2025)
        with patch(
            "cli.obter_configuracao_endpoint",
            return_value={
                "endpoint": "deputados/{id}/despesas",
                "depende_de": "deputados",
                "campo_id": "id",
                "paginacao": True,
                "itens": 5000,
            },
        ):
            with patch("extracao.camara.deputados_federais.Despesas") as extrator_cls:
                cli.handle_extrair_dependentes(args)

        extrator_cls.assert_called_once_with(
            "deputados_despesas",
            {
                "endpoint": "deputados/{id}/despesas",
                "depende_de": "deputados",
                "campo_id": "id",
                "paginacao": True,
                "itens": 5000,
            },
        )
        extrator_cls.return_value.executar.assert_called_once_with(
            ano_inicio=2023,
            ano_fim=2025,
        )

    def test_portal_handle_pipeline_repassa_parametros(self):
        """O handler do Portal deve encaminhar filtros para o orquestrador."""

        args = SimpleNamespace(
            limit_fornecedores=11,
            min_ocorrencias=4,
            ano_inicio=2020,
            ano_fim=2024,
            fases=[1, 2],
        )
        with patch("pipeline.PipelinePortalTransparencia") as pipeline_cls:
            cli.handle_rodar_pipeline_portal(args)

        pipeline_cls.assert_called_once_with(
            limit_fornecedores=11,
            min_ocorrencias=4,
            ano_inicio=2020,
            ano_fim=2024,
            fases=[1, 2],
        )
        pipeline_cls.return_value.executar.assert_called_once_with()

    def test_pipelines_handlers_repassam_overrides(self):
        """Os handlers de orquestração devem propagar os argumentos da CLI."""

        args_paralelo = SimpleNamespace(
            ano_inicio=2021,
            ano_fim=2024,
            pncp_data_inicial="2024-01-01",
            pncp_data_final="2024-12-31",
            max_workers=6,
            incluir_camara=True,
            incluir_senado=False,
            incluir_siop=True,
            incluir_ibge=False,
            incluir_pncp=True,
            incluir_transferegov=False,
            incluir_obrasgov=True,
            incluir_siconfi=None,
        )
        args_completo = SimpleNamespace(
            ano_inicio=2020,
            ano_fim=2025,
            max_workers=8,
            incluir_portal=False,
            incluir_anp=True,
            incluir_obrasgov_geometrias=None,
        )

        with patch("pipeline.PipelineParalelo") as paralelo_cls:
            cli.handle_rodar_paralelo(args_paralelo)
        with patch("pipeline.PipelineCompleto") as completo_cls:
            cli.handle_rodar_pipeline_completo(args_completo)

        paralelo_kwargs = paralelo_cls.call_args.kwargs
        self.assertEqual(str(paralelo_kwargs["pncp_data_inicial"]), "2024-01-01")
        self.assertEqual(str(paralelo_kwargs["pncp_data_final"]), "2024-12-31")
        self.assertEqual(paralelo_kwargs["max_workers"], 6)
        self.assertTrue(paralelo_kwargs["incluir_camara"])
        self.assertFalse(paralelo_kwargs["incluir_senado"])
        paralelo_cls.return_value.executar.assert_called_once_with()

        completo_cls.assert_called_once_with(
            ano_inicio=2020,
            ano_fim=2025,
            max_workers=8,
            incluir_portal=False,
            incluir_anp=True,
            incluir_obrasgov_geometrias=None,
        )
        completo_cls.return_value.executar.assert_called_once_with()

    def test_fontes_handle_obrasgov_normaliza_filtros_antes_de_executar(self):
        """O handler do ObrasGov deve converter filtros CLI antes de chamar o extrator."""

        args = SimpleNamespace(
            filtro=["uf=sp"],
            recursos=["projetos"],
            tamanho_pagina=77,
        )
        with patch("utils.filtros.parse_filtros_cli", return_value={"uf": "sp"}) as parse_cls:
            with patch("extracao.obrasgov.ObrasGov") as obras_cls:
                cli.handle_extrair_obrasgov(args)

        parse_cls.assert_called_once_with(["uf=sp"])
        obras_cls.assert_called_once_with(page_size=77)
        obras_cls.return_value.executar_recursos.assert_called_once_with(
            recursos=["projetos"],
            filtros={"uf": "sp"},
        )

    def test_fontes_handle_siconfi_valida_filtros_e_executa(self):
        """O handler do Siconfi deve delegar filtros e recursos ao pacote."""

        args = SimpleNamespace(
            recursos=["entes"],
            filtro=["id_ente=3550308"],
            tamanho_pagina=33,
        )
        with patch("utils.filtros.parse_filtros_cli", return_value={"id_ente": "3550308"}):
            with patch("extracao.siconfi.preparar_consultas_siconfi") as preparar_cls:
                with patch("extracao.siconfi.Siconfi") as siconfi_cls:
                    cli.handle_extrair_siconfi(args)

        preparar_cls.assert_called_once_with(["entes"], {"id_ente": "3550308"})
        siconfi_cls.assert_called_once_with(page_size=33)
        siconfi_cls.return_value.executar.assert_called_once_with(
            recursos=["entes"],
            filtros={"id_ente": "3550308"},
        )

    def test_fontes_handle_anp_delega_toda_orquestracao_ao_pacote(self):
        """O handler da ANP não deve reconstruir estado fora do orquestrador."""

        args = SimpleNamespace(
            datasets=["combustivel"],
            min_ocorrencias=5,
            limit_fornecedores=9,
        )
        with patch("extracao.anp.RevendedoresANP") as anp_cls:
            cli.handle_extrair_anp(args)

        anp_cls.assert_called_once_with(
            min_ocorrencias=5,
            limit_fornecedores=9,
        )
        anp_cls.return_value.executar.assert_called_once_with(datasets=["combustivel"])

    def test_fontes_handle_transferegov_delega_ao_pacote_publico(self):
        """O handler do Transferegov deve usar a fachada pública do pacote."""

        args = SimpleNamespace(
            filtro=["uf=sp"],
            recursos=["programa_especial"],
            tamanho_pagina=150,
        )
        with patch("utils.filtros.parse_filtros_cli", return_value={"uf": "sp"}) as parse_cls:
            with patch("extracao.transferegov.TransferegovRecursos") as recursos_cls:
                cli._handle_extrair_transferegov(args, "especial")

        parse_cls.assert_called_once_with(["uf=sp"])
        recursos_cls.assert_called_once_with(grupo="especial", page_size=150)
        recursos_cls.return_value.executar.assert_called_once_with(
            recursos=["programa_especial"],
            filtros={"uf": "sp"},
        )

    def test_fontes_handle_senado_delega_ao_pacote_publico(self):
        """O handler do Senado deve usar a fachada pública do pacote."""

        args = SimpleNamespace(endpoint="ceaps")
        with patch("extracao.senado.DadosSenado") as senado_cls:
            cli.handle_extrair_senado(args)

        senado_cls.assert_called_once_with("ceaps")
        senado_cls.return_value.executar.assert_called_once_with()

    def test_fontes_handle_ibge_delega_ao_pacote_publico(self):
        """O handler do IBGE deve usar a fachada pública do pacote."""

        args = SimpleNamespace(datasets=["estados", "municipios"])
        with patch("extracao.ibge.LocalidadesIBGE") as ibge_cls:
            cli.handle_extrair_ibge_localidades(args)

        ibge_cls.assert_called_once_with()
        ibge_cls.return_value.executar.assert_called_once_with(
            datasets=["estados", "municipios"]
        )

    def test_fontes_handle_pncp_delega_ao_pacote_publico(self):
        """O handler do PNCP deve usar a fachada pública do pacote."""

        args = SimpleNamespace(
            tamanho_pagina=55,
            data_inicial="2025-01-01",
            data_final="2025-12-31",
            sem_contratos=False,
            sem_atas=True,
            sem_pca=False,
            codigo_classificacao_superior="1234",
        )
        with patch("extracao.pncp.PNCPConsulta") as pncp_cls:
            cli.handle_extrair_pncp(args)

        pncp_cls.assert_called_once_with(page_size=55)
        pncp_cls.return_value.executar.assert_called_once_with(
            data_inicial=cli.parse_data_iso("2025-01-01"),
            data_final=cli.parse_data_iso("2025-12-31"),
            incluir_contratos=True,
            incluir_atas=False,
            incluir_pca=True,
            codigo_classificacao_superior="1234",
        )


if __name__ == "__main__":
    unittest.main()
