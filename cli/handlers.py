"""Handlers dos comandos da CLI."""

from __future__ import annotations

import argparse
import os
import subprocess
from typing import Callable

from configuracao.endpoint import obter_configuracao_endpoint
from configuracao.projeto import PROJECT_ROOT
from extracao.anp.revendedores import ExtratorRevendedoresANP
from extracao.camara.deputados_federais.dependente import ExtratorDependente
from extracao.camara.deputados_federais.deputados import ExtratorDeputadosLegislatura
from extracao.camara.deputados_federais.extrator_legislatura import ExtratorLegislaturas
from extracao.ibge.localidades import ExtratorLocalidadesIBGE
from extracao.obrasgov.obras import ExtratorObrasGov
from extracao.pncp.consultas import ExtratorPNCPConsulta
from extracao.portal.fornecedores import ConstrutorDimFornecedoresPortal
from extracao.senado.senadores import ExtratorDadosSenado
from extracao.siconfi.api import ExtratorSiconfi
from extracao.siop.extrator import ExtratorSIOP
from extracao.transferegov.recursos import ExtratorTransferegovRecursos
from pipeline import PipelineCamara
from pipeline_completo import PipelineCompleto
from pipeline_paralelo import PipelineParalelo
from pipeline_portal import PipelinePortalTransparencia
from utils.csv.orquestrador_csv import OrquestradorGeracaoCSVs
from utils.filtros import parse_filtros_cli

from .common import parse_data_iso

CommandHandler = Callable[[argparse.Namespace], None]


def _binario_cidadao_de_olho(app_dir, release: bool):
    """Resolve o caminho do binario compilado do app web."""

    perfil = "release" if release else "debug"
    return app_dir / "target" / perfil / "cidadao_de_olho-cli"


def _binario_cidadao_de_olho_esta_atualizado(app_dir, binario) -> bool:
    """Verifica se o binario e mais novo do que as fontes Rust do app."""

    if not binario.exists():
        return False

    referencias = [
        app_dir / "Cargo.toml",
        app_dir / "Cargo.lock",
        *sorted((app_dir / "src").rglob("*.rs")),
    ]
    instante_referencia = max(
        caminho.stat().st_mtime for caminho in referencias if caminho.exists()
    )
    return binario.stat().st_mtime >= instante_referencia


def handle_menu(_: argparse.Namespace):
    """Abre o menu interativo do terminal."""

    from .menu import open_terminal_menu

    open_terminal_menu()


def handle_servir_cidadao_de_olho(args: argparse.Namespace):
    """Sobe a aplicacao publica Olho Cidadão baseada em Loco.rs."""

    app_dir = PROJECT_ROOT / "apps" / "cidadao_de_olho"
    manifest_path = app_dir / "Cargo.toml"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Aplicacao Loco.rs nao encontrada em {manifest_path}."
        )

    ambiente = os.environ.copy()
    ambiente["LOCO_ENV"] = args.ambiente
    binario = _binario_cidadao_de_olho(app_dir, args.release)

    try:
        if not _binario_cidadao_de_olho_esta_atualizado(app_dir, binario):
            comando_build = ["cargo", "build", "--manifest-path", str(manifest_path)]
            if args.release:
                comando_build.append("--release")

            subprocess.run(
                comando_build,
                cwd=app_dir,
                env=ambiente,
                check=True,
            )

        subprocess.run(
            [str(binario), "start"],
            cwd=app_dir,
            env=ambiente,
            check=True,
        )
    except KeyboardInterrupt:
        return


def handle_gerar_csv(args: argparse.Namespace):
    """Executa todos os geradores de CSV registrados no projeto."""

    OrquestradorGeracaoCSVs(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    ).executar()


def handle_rodar_pipeline(args: argparse.Namespace):
    """Executa o pipeline completo da Câmara."""

    PipelineCamara(ano_inicio=args.ano_inicio, ano_fim=args.ano_fim).executar()


def handle_rodar_paralelo(args: argparse.Namespace):
    """Executa as fontes independentes em paralelo controlado."""

    PipelineParalelo(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        pncp_data_inicial=(
            parse_data_iso(args.pncp_data_inicial) if args.pncp_data_inicial else None
        ),
        pncp_data_final=(
            parse_data_iso(args.pncp_data_final) if args.pncp_data_final else None
        ),
        max_workers=args.max_workers,
        incluir_camara=args.incluir_camara,
        incluir_senado=args.incluir_senado,
        incluir_siop=args.incluir_siop,
        incluir_ibge=args.incluir_ibge,
        incluir_pncp=args.incluir_pncp,
        incluir_transferegov=args.incluir_transferegov,
        incluir_obrasgov=args.incluir_obrasgov,
        incluir_siconfi=args.incluir_siconfi,
    ).executar()


def handle_rodar_pipeline_completo(args: argparse.Namespace):
    """Executa o pipeline completo configurado no `etl-config.toml`."""

    PipelineCompleto(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        max_workers=args.max_workers,
        incluir_portal=args.incluir_portal,
        incluir_anp=args.incluir_anp,
        incluir_obrasgov_geometrias=args.incluir_obrasgov_geometrias,
    ).executar()


def handle_baixar_legislaturas(_: argparse.Namespace):
    """Baixa a lista base de legislaturas da Câmara."""

    ExtratorLegislaturas().executar()


def handle_extrair_legislaturas(_: argparse.Namespace):
    """Expande os deputados associados a cada legislatura."""

    ExtratorDeputadosLegislatura().executar()


def handle_extrair_dependentes(args: argparse.Namespace):
    """Extrai dados dependentes da Câmara, como despesas."""

    config = obter_configuracao_endpoint(args.endpoint)
    ExtratorDependente(args.endpoint, config).executar(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
    )


def handle_extrair_senado(args: argparse.Namespace):
    """Extrai os dados configurados do Senado."""

    config = obter_configuracao_endpoint(args.endpoint)
    ExtratorDadosSenado(
        nome_endpoint=args.endpoint,
        configuracao=config,
    ).executar()


def handle_extrair_siop(_: argparse.Namespace):
    """Extrai o dataset orçamentário do SIOP."""

    ExtratorSIOP().executar()


def handle_portal_construir_fornecedores(args: argparse.Namespace):
    """Reconstrói a dimensão local de fornecedores do Portal."""

    PipelinePortalTransparencia(min_ocorrencias=args.min_ocorrencias).executar_dimensao()


def handle_extrair_portal_documentos(args: argparse.Namespace):
    """Extrai documentos por favorecido do Portal da Transparência."""

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        fases=args.fases,
    ).executar_documentos()


def handle_extrair_portal_sancoes(args: argparse.Namespace):
    """Extrai CEIS, CNEP e CEPIM para os fornecedores selecionados."""

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
    ).executar_sancoes()


def handle_extrair_portal_notas_fiscais(args: argparse.Namespace):
    """Extrai notas fiscais do Portal da Transparência."""

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
    ).executar_notas_fiscais()


def handle_rodar_pipeline_portal(args: argparse.Namespace):
    """Executa a pipeline completa do Portal da Transparência."""

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        fases=args.fases,
    ).executar()


def handle_extrair_ibge_localidades(args: argparse.Namespace):
    """Extrai regiões, estados e municípios do IBGE."""

    ExtratorLocalidadesIBGE().executar(datasets=args.datasets)


def handle_extrair_pncp(args: argparse.Namespace):
    """Extrai contratos, atas e PCA do PNCP."""

    ExtratorPNCPConsulta(page_size=args.tamanho_pagina).executar(
        data_inicial=parse_data_iso(args.data_inicial),
        data_final=parse_data_iso(args.data_final),
        incluir_contratos=not args.sem_contratos,
        incluir_atas=not args.sem_atas,
        incluir_pca=not args.sem_pca,
        codigo_classificacao_superior=args.codigo_classificacao_superior,
    )


def handle_extrair_transferegov(args: argparse.Namespace, grupo: str):
    """Extrai um grupo de recursos do Transferegov."""

    filtros = parse_filtros_cli(args.filtro)
    ExtratorTransferegovRecursos(
        grupo=grupo,
        page_size=args.tamanho_pagina,
    ).executar(recursos=args.recursos, filtros=filtros)


def handle_extrair_obrasgov(args: argparse.Namespace):
    """Extrai projetos e execuções do ObrasGov."""

    filtros = parse_filtros_cli(args.filtro)
    ExtratorObrasGov(page_size=args.tamanho_pagina).executar_recursos(
        recursos=args.recursos,
        filtros=filtros,
    )


def handle_extrair_obrasgov_geometrias(args: argparse.Namespace):
    """Extrai as geometrias de projetos já persistidos no ObrasGov."""

    ExtratorObrasGov().executar_geometrias(limit_ids=args.limit_ids)


def handle_extrair_siconfi(args: argparse.Namespace):
    """Extrai recursos configurados do Siconfi."""

    filtros = parse_filtros_cli(args.filtro)
    ExtratorSiconfi(page_size=args.tamanho_pagina).executar(
        recursos=args.recursos,
        filtros=filtros,
    )


def handle_extrair_anp(args: argparse.Namespace):
    """Extrai revendedores ANP a partir da dimensão local de fornecedores."""

    ConstrutorDimFornecedoresPortal().construir(min_ocorrencias=args.min_ocorrencias)
    ExtratorRevendedoresANP(
        min_ocorrencias=args.min_ocorrencias,
        limit_fornecedores=args.limit_fornecedores,
    ).executar(datasets=args.datasets)


HANDLERS: dict[str, CommandHandler] = {
    "menu": handle_menu,
    "abrir-menu": handle_menu,
    "servir-cidadao-de-olho": handle_servir_cidadao_de_olho,
    "abrir-cidadao-de-olho": handle_servir_cidadao_de_olho,
    "gerar-csv": handle_gerar_csv,
    "rodar-pipeline": handle_rodar_pipeline,
    "rodar-paralelo": handle_rodar_paralelo,
    "rodar-pipeline-completo": handle_rodar_pipeline_completo,
    "baixar-legislaturas": handle_baixar_legislaturas,
    "extrair-legislaturas": handle_extrair_legislaturas,
    "extrair-dependentes": handle_extrair_dependentes,
    "extrair-senado": handle_extrair_senado,
    "extrair-siop": handle_extrair_siop,
    "portal-construir-fornecedores": handle_portal_construir_fornecedores,
    "extrair-portal-documentos": handle_extrair_portal_documentos,
    "extrair-portal-sancoes": handle_extrair_portal_sancoes,
    "extrair-portal-notas-fiscais": handle_extrair_portal_notas_fiscais,
    "rodar-pipeline-portal": handle_rodar_pipeline_portal,
    "extrair-ibge-localidades": handle_extrair_ibge_localidades,
    "extrair-pncp": handle_extrair_pncp,
    "extrair-transferegov-especial": lambda ns: handle_extrair_transferegov(ns, "especial"),
    "extrair-transferegov-fundo": lambda ns: handle_extrair_transferegov(ns, "fundoafundo"),
    "extrair-transferegov-ted": lambda ns: handle_extrair_transferegov(ns, "ted"),
    "extrair-obrasgov": handle_extrair_obrasgov,
    "extrair-obrasgov-geometrias": handle_extrair_obrasgov_geometrias,
    "extrair-siconfi": handle_extrair_siconfi,
    "extrair-anp": handle_extrair_anp,
}
