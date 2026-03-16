"""Construção da CLI principal do projeto."""

from __future__ import annotations

import argparse
from typing import Any

from configuracao.projeto import obter_parametros_cli
from configuracao.projeto import resolver_data_configurada_iso
from extracao.anp.revendedores import ANP_DATASETS
from extracao.obrasgov.obras import PAGEABLE_RESOURCES
from extracao.siconfi.api import SICONFI_RESOURCES
from extracao.transferegov.recursos import RESOURCE_GROUPS

from .common import adicionar_args_intervalo_anos
from .common import adicionar_flag_inclusao


def _registrar_comandos_camara(subparsers: Any):
    """Registra os comandos relacionados à Câmara."""

    config_csv = obter_parametros_cli("gerar_csv")

    parser_csv = subparsers.add_parser(
        "gerar-csv",
        help="Gera o arquivo CSV consolidado das despesas.",
    )
    parser_csv.add_argument(
        "--data-dir",
        default=config_csv.get("data_dir"),
        help="Diretório raiz dos dados.",
    )
    parser_csv.add_argument(
        "--output-dir",
        default=config_csv.get("output_dir"),
        help="Onde salvar o CSV final.",
    )

    subparsers.add_parser(
        "extrair-legislaturas",
        help="Extrai os deputados vinculados às legislaturas.",
    )
    subparsers.add_parser(
        "baixar-legislaturas",
        help="Baixa o arquivo base com IDs de legislaturas.",
    )

    parser_dep = subparsers.add_parser(
        "extrair-dependentes",
        help="Extrai dados dependentes (ex: despesas).",
    )
    parser_dep.add_argument("--endpoint", required=True, help="Nome do endpoint no config.")
    adicionar_args_intervalo_anos(parser_dep)

    parser_pipeline = subparsers.add_parser(
        "rodar-pipeline",
        help="Executa o pipeline completo da Câmara.",
    )
    adicionar_args_intervalo_anos(parser_pipeline, usar_defaults_compartilhados=False)


def _registrar_comando_menu(subparsers: Any):
    """Registra o menu interativo do terminal."""

    subparsers.add_parser(
        "menu",
        aliases=["abrir-menu"],
        help="Abre um menu interativo para navegar pelas funcionalidades da CLI.",
    )


def _registrar_comando_cidadao_de_olho(subparsers: Any):
    """Registra o comando que sobe a aplicacao publica Loco.rs."""

    parser_web = subparsers.add_parser(
        "servir-cidadao-de-olho",
        aliases=["abrir-cidadao-de-olho"],
        help="Inicia a aplicacao publica Olho Cidadão em Loco.rs.",
    )
    parser_web.add_argument(
        "--ambiente",
        choices=["development", "production", "test"],
        default="development",
        help="Perfil de configuracao do app Loco.rs.",
    )
    parser_web.add_argument(
        "--release",
        action="store_true",
        help="Compila e executa o app web em modo release.",
    )


def _registrar_comandos_portal(subparsers: Any):
    """Registra os comandos do Portal da Transparência."""

    config_portal = obter_parametros_cli("portal")

    parser_portal_fornecedores = subparsers.add_parser(
        "portal-construir-fornecedores",
        help=(
            "Constrói a dimensão de fornecedores para enriquecimento com o "
            "Portal da Transparência."
        ),
    )
    parser_portal_fornecedores.add_argument(
        "--min-ocorrencias",
        type=int,
        default=config_portal.get("min_ocorrencias"),
    )

    parser_portal_documentos = subparsers.add_parser(
        "extrair-portal-documentos",
        help="Extrai documentos por favorecido do Portal da Transparência.",
    )
    parser_portal_documentos.add_argument(
        "--min-ocorrencias",
        type=int,
        default=config_portal.get("min_ocorrencias"),
    )
    parser_portal_documentos.add_argument("--limit-fornecedores", type=int, default=None)
    parser_portal_documentos.add_argument("--ano-inicio", type=int, default=None)
    parser_portal_documentos.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo para documentos por favorecido.",
    )
    parser_portal_documentos.add_argument(
        "--fases",
        type=int,
        nargs="*",
        default=config_portal.get("fases"),
        help="Fases para consultar no endpoint documentos-por-favorecido.",
    )

    parser_portal_sancoes = subparsers.add_parser(
        "extrair-portal-sancoes",
        help="Extrai CEIS, CNEP e CEPIM para os fornecedores encontrados no projeto.",
    )
    parser_portal_sancoes.add_argument(
        "--min-ocorrencias",
        type=int,
        default=config_portal.get("min_ocorrencias"),
    )
    parser_portal_sancoes.add_argument("--limit-fornecedores", type=int, default=None)

    parser_portal_notas = subparsers.add_parser(
        "extrair-portal-notas-fiscais",
        help="Extrai notas fiscais do Portal da Transparência por CNPJ emitente.",
    )
    parser_portal_notas.add_argument(
        "--min-ocorrencias",
        type=int,
        default=config_portal.get("min_ocorrencias"),
    )
    parser_portal_notas.add_argument("--limit-fornecedores", type=int, default=None)

    parser_pipeline_portal = subparsers.add_parser(
        "rodar-pipeline-portal",
        help="Executa a pipeline completa de enriquecimento com o Portal da Transparência.",
    )
    parser_pipeline_portal.add_argument(
        "--min-ocorrencias",
        type=int,
        default=config_portal.get("min_ocorrencias"),
    )
    parser_pipeline_portal.add_argument("--limit-fornecedores", type=int, default=None)
    parser_pipeline_portal.add_argument("--ano-inicio", type=int, default=None)
    parser_pipeline_portal.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo para documentos por favorecido.",
    )
    parser_pipeline_portal.add_argument(
        "--fases",
        type=int,
        nargs="*",
        default=config_portal.get("fases"),
        help="Fases para consultar no endpoint documentos-por-favorecido.",
    )


def _registrar_comandos_paralelos(subparsers: Any):
    """Registra os comandos de orquestração paralela e fontes independentes."""

    config_extrair_senado = obter_parametros_cli("extrair_senado")
    config_extrair_ibge = obter_parametros_cli("extrair_ibge_localidades")
    config_extrair_pncp = obter_parametros_cli("extrair_pncp")
    config_extrair_transferegov = obter_parametros_cli("extrair_transferegov")
    config_extrair_obrasgov = obter_parametros_cli("extrair_obrasgov")
    config_extrair_siconfi = obter_parametros_cli("extrair_siconfi")
    config_extrair_anp = obter_parametros_cli("extrair_anp")

    parser_pipeline_paralelo = subparsers.add_parser(
        "rodar-paralelo",
        help="Executa em paralelo as extrações que não dependem umas das outras.",
    )
    adicionar_args_intervalo_anos(
        parser_pipeline_paralelo,
        usar_defaults_compartilhados=False,
    )
    parser_pipeline_paralelo.add_argument(
        "--pncp-data-inicial",
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    parser_pipeline_paralelo.add_argument(
        "--pncp-data-final",
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    parser_pipeline_paralelo.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="camara",
        destino="incluir_camara",
        descricao="a fonte Camara",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="senado",
        destino="incluir_senado",
        descricao="a fonte Senado",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="siop",
        destino="incluir_siop",
        descricao="a fonte SIOP",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="ibge",
        destino="incluir_ibge",
        descricao="a fonte IBGE",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="pncp",
        destino="incluir_pncp",
        descricao="a fonte PNCP",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="transferegov",
        destino="incluir_transferegov",
        descricao="a fonte Transferegov",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="obrasgov",
        destino="incluir_obrasgov",
        descricao="a fonte ObrasGov",
    )
    adicionar_flag_inclusao(
        parser_pipeline_paralelo,
        nome="siconfi",
        destino="incluir_siconfi",
        descricao="a fonte Siconfi",
    )

    parser_pipeline_completo = subparsers.add_parser(
        "rodar-pipeline-completo",
        help="Executa a extração completa em fases, usando a configuração do etl-config.toml.",
    )
    parser_pipeline_completo.add_argument("--ano-inicio", type=int, default=None)
    parser_pipeline_completo.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo. Se omitido, usa a configuração do pipeline.",
    )
    parser_pipeline_completo.add_argument("--max-workers", type=int, default=None)
    adicionar_flag_inclusao(
        parser_pipeline_completo,
        nome="portal",
        destino="incluir_portal",
        descricao="o enriquecimento do Portal da Transparencia",
    )
    adicionar_flag_inclusao(
        parser_pipeline_completo,
        nome="anp",
        destino="incluir_anp",
        descricao="o enriquecimento da ANP",
    )
    adicionar_flag_inclusao(
        parser_pipeline_completo,
        nome="obrasgov-geometrias",
        destino="incluir_obrasgov_geometrias",
        descricao="as geometrias do ObrasGov",
    )

    parser_senado = subparsers.add_parser(
        "extrair-senado",
        help="Extrai dados do Senado Federal (ex: CEAPS).",
    )
    parser_senado.add_argument(
        "--endpoint",
        default=config_extrair_senado.get("endpoint"),
        help="Nome do endpoint no config (padrão: ceaps).",
    )

    subparsers.add_parser(
        "extrair-siop",
        help="Extrai dados orçamentários do endpoint SPARQL do SIOP.",
    )

    parser_ibge = subparsers.add_parser(
        "extrair-ibge-localidades",
        help="Extrai regiões, estados e municípios da API de localidades do IBGE.",
    )
    parser_ibge.add_argument(
        "--datasets",
        nargs="*",
        choices=["regioes", "estados", "municipios"],
        default=config_extrair_ibge.get("datasets"),
    )

    parser_pncp = subparsers.add_parser(
        "extrair-pncp",
        help="Extrai contratos, atas e PCA da API pública do PNCP.",
    )
    parser_pncp.add_argument(
        "--data-inicial",
        default=resolver_data_configurada_iso(config_extrair_pncp.get("data_inicial")),
    )
    parser_pncp.add_argument(
        "--data-final",
        default=resolver_data_configurada_iso(config_extrair_pncp.get("data_final")),
    )
    parser_pncp.add_argument(
        "--tamanho-pagina",
        type=int,
        default=config_extrair_pncp.get("tamanho_pagina"),
    )
    parser_pncp.add_argument("--codigo-classificacao-superior", default=None)
    parser_pncp.add_argument("--sem-contratos", action="store_true")
    parser_pncp.add_argument("--sem-atas", action="store_true")
    parser_pncp.add_argument("--sem-pca", action="store_true")

    parser_transf_especial = subparsers.add_parser(
        "extrair-transferegov-especial",
        help="Extrai datasets da API de Transferências Especiais do Transferegov.",
    )
    parser_transf_especial.add_argument(
        "--recursos",
        nargs="*",
        choices=RESOURCE_GROUPS["especial"],
        default=None,
    )
    parser_transf_especial.add_argument("--filtro", action="append", default=[])
    parser_transf_especial.add_argument(
        "--tamanho-pagina",
        type=int,
        default=config_extrair_transferegov.get("tamanho_pagina"),
    )

    parser_transf_fundo = subparsers.add_parser(
        "extrair-transferegov-fundo",
        help="Extrai datasets da API Fundo a Fundo do Transferegov.",
    )
    parser_transf_fundo.add_argument(
        "--recursos",
        nargs="*",
        choices=RESOURCE_GROUPS["fundoafundo"],
        default=None,
    )
    parser_transf_fundo.add_argument("--filtro", action="append", default=[])
    parser_transf_fundo.add_argument(
        "--tamanho-pagina",
        type=int,
        default=config_extrair_transferegov.get("tamanho_pagina"),
    )

    parser_transf_ted = subparsers.add_parser(
        "extrair-transferegov-ted",
        help="Extrai datasets da API TED do Transferegov.",
    )
    parser_transf_ted.add_argument(
        "--recursos",
        nargs="*",
        choices=RESOURCE_GROUPS["ted"],
        default=None,
    )
    parser_transf_ted.add_argument("--filtro", action="append", default=[])
    parser_transf_ted.add_argument(
        "--tamanho-pagina",
        type=int,
        default=config_extrair_transferegov.get("tamanho_pagina"),
    )

    parser_obras = subparsers.add_parser(
        "extrair-obrasgov",
        help="Extrai projetos e execuções da API do ObrasGov.",
    )
    parser_obras.add_argument(
        "--recursos",
        nargs="*",
        choices=list(PAGEABLE_RESOURCES),
        default=None,
    )
    parser_obras.add_argument("--filtro", action="append", default=[])
    parser_obras.add_argument(
        "--tamanho-pagina",
        type=int,
        default=config_extrair_obrasgov.get("tamanho_pagina"),
    )

    parser_obras_geo = subparsers.add_parser(
        "extrair-obrasgov-geometrias",
        help="Extrai geometrias no ObrasGov para os projetos já persistidos.",
    )
    parser_obras_geo.add_argument("--limit-ids", type=int, default=None)

    parser_siconfi = subparsers.add_parser(
        "extrair-siconfi",
        help="Extrai recursos da API de dados abertos do Siconfi.",
    )
    parser_siconfi.add_argument(
        "--recursos",
        nargs="*",
        choices=list(SICONFI_RESOURCES),
        default=config_extrair_siconfi.get("recursos"),
    )
    parser_siconfi.add_argument(
        "--filtro",
        action="append",
        default=[],
        help=(
            "Filtro no formato chave=valor. Pode ser repetido. "
            "Recursos como extrato_entregas, msc_*, rreo, rgf e dca "
            "exigem filtros obrigatórios específicos."
        ),
    )
    parser_siconfi.add_argument(
        "--tamanho-pagina",
        type=int,
        default=config_extrair_siconfi.get("tamanho_pagina"),
    )

    parser_anp = subparsers.add_parser(
        "extrair-anp",
        help="Extrai revendedores autorizados da ANP para os CNPJs do projeto.",
    )
    parser_anp.add_argument(
        "--datasets",
        nargs="*",
        choices=list(ANP_DATASETS),
        default=config_extrair_anp.get("datasets"),
    )
    parser_anp.add_argument(
        "--min-ocorrencias",
        type=int,
        default=config_extrair_anp.get("min_ocorrencias"),
    )
    parser_anp.add_argument("--limit-fornecedores", type=int, default=None)


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser principal da CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "CLI de dados legislativos, orçamentários e de enriquecimento "
            "investigativo com APIs governamentais."
        )
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")
    subparsers.required = True

    _registrar_comando_menu(subparsers)
    _registrar_comando_cidadao_de_olho(subparsers)
    _registrar_comandos_camara(subparsers)
    _registrar_comandos_portal(subparsers)
    _registrar_comandos_paralelos(subparsers)
    return parser
