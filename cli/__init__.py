"""Fachada publica e orquestracao central da CLI do projeto."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from configuracao import PROJECT_ROOT
from configuracao import obter_configuracao_endpoint
from configuracao import obter_parametros_cli
from configuracao import resolver_data_configurada_iso
from configuracao.logger import logger
from infra.errors import UserInputError

from .comun import CliCommand
from .comun import CommandHandler
from .comun import adicionar_arg_filtros
from .comun import adicionar_arg_limit_fornecedores
from .comun import adicionar_arg_min_ocorrencias
from .comun import adicionar_arg_tamanho_pagina
from .comun import adicionar_args_intervalo_anos
from .comun import adicionar_flag_inclusao
from .comun import parse_data_iso


def _configurar_gerar_csv(parser: argparse.ArgumentParser):
    """Configura argumentos do gerador de CSVs."""

    config = obter_parametros_cli("gerar_csv")
    parser.add_argument(
        "--data-dir",
        default=config.get("data_dir"),
        help="Diretório raiz dos dados.",
    )
    parser.add_argument(
        "--output-dir",
        default=config.get("output_dir"),
        help="Diretório raiz onde os CSVs serão salvos.",
    )


def _configurar_extrair_dependentes(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de dados dependentes da Câmara."""

    parser.add_argument("--endpoint", required=True, help="Nome do endpoint no config.")
    adicionar_args_intervalo_anos(parser)


def _configurar_rodar_pipeline(parser: argparse.ArgumentParser):
    """Configura overrides do pipeline da Câmara."""

    adicionar_args_intervalo_anos(parser, usar_defaults_compartilhados=False)


def _configurar_min_ocorrencias(parser: argparse.ArgumentParser):
    """Adiciona apenas o argumento de mínimo de ocorrências."""

    adicionar_arg_min_ocorrencias(
        parser,
        default=obter_parametros_cli("portal").get("min_ocorrencias"),
    )


def _configurar_portal_documentos(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de documentos do Portal."""

    config = obter_parametros_cli("portal")
    adicionar_arg_min_ocorrencias(parser, default=config.get("min_ocorrencias"))
    adicionar_arg_limit_fornecedores(parser)
    parser.add_argument("--ano-inicio", type=int, default=None)
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo para documentos por favorecido.",
    )
    parser.add_argument(
        "--fases",
        type=int,
        nargs="*",
        default=config.get("fases"),
        help="Fases para consultar no endpoint documentos-por-favorecido.",
    )


def _configurar_portal_simples(parser: argparse.ArgumentParser):
    """Configura argumentos comuns a sanções e notas fiscais do Portal."""

    adicionar_arg_min_ocorrencias(
        parser,
        default=obter_parametros_cli("portal").get("min_ocorrencias"),
    )
    adicionar_arg_limit_fornecedores(parser)


def _configurar_rodar_paralelo(parser: argparse.ArgumentParser):
    """Configura argumentos do pipeline paralelo."""

    adicionar_args_intervalo_anos(parser, usar_defaults_compartilhados=False)
    parser.add_argument(
        "--pncp-data-inicial",
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    parser.add_argument(
        "--pncp-data-final",
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Se omitido, usa a configuracao do pipeline paralelo no etl-config.toml.",
    )
    for nome, destino, descricao in (
        ("camara", "incluir_camara", "a fonte Camara"),
        ("senado", "incluir_senado", "a fonte Senado"),
        ("siop", "incluir_siop", "a fonte SIOP"),
        ("ibge", "incluir_ibge", "a fonte IBGE"),
        ("pncp", "incluir_pncp", "a fonte PNCP"),
        ("transferegov", "incluir_transferegov", "a fonte Transferegov"),
        ("obrasgov", "incluir_obrasgov", "a fonte ObrasGov"),
        ("siconfi", "incluir_siconfi", "a fonte Siconfi"),
    ):
        adicionar_flag_inclusao(
            parser,
            nome=nome,
            destino=destino,
            descricao=descricao,
        )


def _configurar_rodar_pipeline_completo(parser: argparse.ArgumentParser):
    """Configura argumentos do pipeline completo."""

    parser.add_argument("--ano-inicio", type=int, default=None)
    parser.add_argument(
        "--ano-fim",
        type=int,
        default=None,
        help="Ano final exclusivo. Se omitido, usa a configuração do pipeline.",
    )
    parser.add_argument("--max-workers", type=int, default=None)
    for nome, destino, descricao in (
        ("portal", "incluir_portal", "o enriquecimento do Portal da Transparencia"),
        ("anp", "incluir_anp", "o enriquecimento da ANP"),
        (
            "obrasgov-geometrias",
            "incluir_obrasgov_geometrias",
            "as geometrias do ObrasGov",
        ),
    ):
        adicionar_flag_inclusao(
            parser,
            nome=nome,
            destino=destino,
            descricao=descricao,
        )


def _configurar_extrair_senado(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do Senado."""

    config = obter_parametros_cli("extrair_senado")
    parser.add_argument(
        "--endpoint",
        default=config.get("endpoint"),
        help="Nome do endpoint no config (padrão: ceaps).",
    )


def _configurar_extrair_ibge(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de localidades do IBGE."""

    from extracao.ibge import IBGE_DATASETS

    config = obter_parametros_cli("extrair_ibge_localidades")
    parser.add_argument(
        "--datasets",
        nargs="*",
        choices=list(IBGE_DATASETS),
        default=config.get("datasets"),
    )


def _configurar_extrair_pncp(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do PNCP."""

    config = obter_parametros_cli("extrair_pncp")
    parser.add_argument(
        "--data-inicial",
        default=resolver_data_configurada_iso(config.get("data_inicial")),
    )
    parser.add_argument(
        "--data-final",
        default=resolver_data_configurada_iso(config.get("data_final")),
    )
    adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))
    parser.add_argument("--codigo-classificacao-superior", default=None)
    parser.add_argument("--sem-contratos", action="store_true")
    parser.add_argument("--sem-atas", action="store_true")
    parser.add_argument("--sem-pca", action="store_true")


def _configurar_extrair_obrasgov(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do ObrasGov."""

    from extracao.obrasgov import PAGEABLE_RESOURCES

    config = obter_parametros_cli("extrair_obrasgov")
    parser.add_argument(
        "--recursos",
        nargs="*",
        choices=list(PAGEABLE_RESOURCES),
        default=None,
    )
    adicionar_arg_filtros(parser)
    adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))


def _configurar_extrair_obrasgov_geometrias(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator de geometrias do ObrasGov."""

    parser.add_argument("--limit-ids", type=int, default=None)


def _configurar_extrair_siconfi(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator do Siconfi."""

    from extracao.siconfi import SICONFI_RESOURCES

    config = obter_parametros_cli("extrair_siconfi")
    parser.add_argument(
        "--recursos",
        nargs="*",
        choices=list(SICONFI_RESOURCES),
        default=config.get("recursos"),
    )
    adicionar_arg_filtros(
        parser,
        help=(
            "Filtro no formato chave=valor. Pode ser repetido. "
            "Recursos como extrato_entregas, msc_*, rreo, rgf e dca "
            "exigem filtros obrigatórios específicos."
        ),
    )
    adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))


def _configurar_extrair_anp(parser: argparse.ArgumentParser):
    """Configura argumentos do extrator da ANP."""

    from extracao.anp import ANP_DATASETS

    config = obter_parametros_cli("extrair_anp")
    parser.add_argument(
        "--datasets",
        nargs="*",
        choices=list(ANP_DATASETS),
        default=config.get("datasets"),
    )
    adicionar_arg_min_ocorrencias(parser, default=config.get("min_ocorrencias"))
    adicionar_arg_limit_fornecedores(parser)


def _configurar_transferegov(grupo: str) -> Callable[[argparse.ArgumentParser], None]:
    """Cria a configuração de parser para um grupo do Transferegov."""

    def configurar(parser: argparse.ArgumentParser):
        from extracao.transferegov import RESOURCE_GROUPS

        config = obter_parametros_cli("extrair_transferegov")
        parser.add_argument(
            "--recursos",
            nargs="*",
            choices=RESOURCE_GROUPS[grupo],
            default=None,
        )
        adicionar_arg_filtros(parser)
        adicionar_arg_tamanho_pagina(parser, default=config.get("tamanho_pagina"))

    return configurar


def _binario_cidadao_de_olho(app_dir: Path, release: bool) -> Path:
    """Resolve o caminho do binário compilado do app web."""

    perfil = "release" if release else "debug"
    return app_dir / "target" / perfil / "cidadao_de_olho-cli"


def _binario_cidadao_de_olho_esta_atualizado(app_dir: Path, binario: Path) -> bool:
    """Verifica se o binário é mais novo do que as fontes Rust do app."""

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


def _configurar_servir_cidadao_de_olho(parser: argparse.ArgumentParser):
    """Configura argumentos do app web público."""

    parser.add_argument(
        "--ambiente",
        choices=["development", "production", "test"],
        default="development",
        help="Perfil de configuracao do app Loco.rs.",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Compila e executa o app web em modo release.",
    )


def _handle_extrair_transferegov(args: argparse.Namespace, grupo: str):
    """Extrai um grupo de recursos do Transferegov."""

    from extracao.transferegov import TransferegovRecursos
    from utils.filtros import parse_filtros_cli

    filtros = parse_filtros_cli(args.filtro)
    TransferegovRecursos(
        grupo=grupo,
        page_size=args.tamanho_pagina,
    ).executar(recursos=args.recursos, filtros=filtros)


def _criar_comando_transferegov(*, nome: str, grupo: str, help: str) -> CliCommand:
    """Cria um comando do Transferegov sem duplicar handler e parser."""

    return CliCommand(
        name=nome,
        help=help,
        handler=lambda args, grupo=grupo: _handle_extrair_transferegov(args, grupo),
        configure_parser=_configurar_transferegov(grupo),
    )


def handle_menu(_: argparse.Namespace):
    """Abre o menu interativo do terminal."""

    from .menu import open_terminal_menu

    open_terminal_menu()


def handle_servir_cidadao_de_olho(args: argparse.Namespace):
    """Sobe a aplicação pública Olho Cidadão baseada em Loco.rs."""

    app_dir = PROJECT_ROOT / "apps" / "cidadao_de_olho"
    manifest_path = app_dir / "Cargo.toml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Aplicacao Loco.rs nao encontrada em {manifest_path}.")

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

    from utils.csv.orquestrador_csv import OrquestradorGeracaoCSVs

    OrquestradorGeracaoCSVs(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
    ).executar()


def handle_baixar_legislaturas(_: argparse.Namespace):
    """Baixa a lista base de legislaturas da Câmara."""

    from extracao.camara.deputados_federais import Legislatura

    Legislatura().executar()


def handle_extrair_legislaturas(_: argparse.Namespace):
    """Expande os deputados associados a cada legislatura."""

    from extracao.camara.deputados_federais import DeputadosLegislatura

    DeputadosLegislatura().executar()


def handle_extrair_dependentes(args: argparse.Namespace):
    """Extrai dados dependentes da Câmara, como despesas."""

    from extracao.camara.deputados_federais import Despesas

    config = obter_configuracao_endpoint(args.endpoint)
    Despesas(args.endpoint, config).executar(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
    )


def handle_rodar_pipeline(args: argparse.Namespace):
    """Executa o pipeline completo da Câmara."""

    from pipeline import PipelineCamara

    PipelineCamara(ano_inicio=args.ano_inicio, ano_fim=args.ano_fim).executar()


def handle_portal_construir_fornecedores(args: argparse.Namespace):
    """Reconstrói a dimensão local de fornecedores do Portal."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(min_ocorrencias=args.min_ocorrencias).executar_dimensao()


def handle_extrair_portal_documentos(args: argparse.Namespace):
    """Extrai documentos por favorecido do Portal da Transparência."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        fases=args.fases,
    ).executar_documentos()


def handle_extrair_portal_sancoes(args: argparse.Namespace):
    """Extrai CEIS, CNEP e CEPIM para os fornecedores selecionados."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
    ).executar_sancoes()


def handle_extrair_portal_notas_fiscais(args: argparse.Namespace):
    """Extrai notas fiscais do Portal da Transparência."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
    ).executar_notas_fiscais()


def handle_rodar_pipeline_portal(args: argparse.Namespace):
    """Executa a pipeline completa do Portal da Transparência."""

    from pipeline import PipelinePortalTransparencia

    PipelinePortalTransparencia(
        limit_fornecedores=args.limit_fornecedores,
        min_ocorrencias=args.min_ocorrencias,
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        fases=args.fases,
    ).executar()


def handle_rodar_paralelo(args: argparse.Namespace):
    """Executa as fontes independentes em paralelo controlado."""

    from pipeline import PipelineParalelo

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

    from pipeline import PipelineCompleto

    PipelineCompleto(
        ano_inicio=args.ano_inicio,
        ano_fim=args.ano_fim,
        max_workers=args.max_workers,
        incluir_portal=args.incluir_portal,
        incluir_anp=args.incluir_anp,
        incluir_obrasgov_geometrias=args.incluir_obrasgov_geometrias,
    ).executar()


def handle_extrair_senado(args: argparse.Namespace):
    """Extrai os dados configurados do Senado."""

    from extracao.senado import DadosSenado

    DadosSenado(args.endpoint).executar()


def handle_extrair_siop(_: argparse.Namespace):
    """Extrai o dataset orçamentário do SIOP."""

    from extracao.siop import SIOP

    SIOP().executar()


def handle_extrair_ibge_localidades(args: argparse.Namespace):
    """Extrai regiões, estados e municípios do IBGE."""

    from extracao.ibge import LocalidadesIBGE

    LocalidadesIBGE().executar(datasets=args.datasets)


def handle_extrair_pncp(args: argparse.Namespace):
    """Extrai contratos, atas e PCA do PNCP."""

    from extracao.pncp import PNCPConsulta

    PNCPConsulta(page_size=args.tamanho_pagina).executar(
        data_inicial=parse_data_iso(args.data_inicial),
        data_final=parse_data_iso(args.data_final),
        incluir_contratos=not args.sem_contratos,
        incluir_atas=not args.sem_atas,
        incluir_pca=not args.sem_pca,
        codigo_classificacao_superior=args.codigo_classificacao_superior,
    )


def handle_extrair_obrasgov(args: argparse.Namespace):
    """Extrai projetos e execuções do ObrasGov."""

    from extracao.obrasgov import ObrasGov
    from utils.filtros import parse_filtros_cli

    filtros = parse_filtros_cli(args.filtro)
    ObrasGov(page_size=args.tamanho_pagina).executar_recursos(
        recursos=args.recursos,
        filtros=filtros,
    )


def handle_extrair_obrasgov_geometrias(args: argparse.Namespace):
    """Extrai as geometrias de projetos já persistidos no ObrasGov."""

    from extracao.obrasgov import ObrasGov

    ObrasGov().executar_geometrias(limit_ids=args.limit_ids)


def handle_extrair_siconfi(args: argparse.Namespace):
    """Extrai recursos configurados do Siconfi."""

    from extracao.siconfi import Siconfi
    from extracao.siconfi import preparar_consultas_siconfi
    from utils.filtros import parse_filtros_cli

    filtros = parse_filtros_cli(args.filtro)
    preparar_consultas_siconfi(args.recursos, filtros)
    Siconfi(page_size=args.tamanho_pagina).executar(
        recursos=args.recursos,
        filtros=filtros,
    )


def handle_extrair_anp(args: argparse.Namespace):
    """Extrai revendedores ANP a partir da dimensão local de fornecedores."""

    from extracao.anp import RevendedoresANP

    RevendedoresANP(
        min_ocorrencias=args.min_ocorrencias,
        limit_fornecedores=args.limit_fornecedores,
    ).executar(datasets=args.datasets)


COMMANDS: tuple[CliCommand, ...] = (
    CliCommand(
        name="menu",
        aliases=("abrir-menu",),
        help="Abre um menu interativo para navegar pelas funcionalidades da CLI.",
        handler=handle_menu,
    ),
    CliCommand(
        name="servir-cidadao-de-olho",
        aliases=("abrir-cidadao-de-olho",),
        help="Inicia a aplicacao publica Olho Cidadão em Loco.rs.",
        handler=handle_servir_cidadao_de_olho,
        configure_parser=_configurar_servir_cidadao_de_olho,
    ),
    CliCommand(
        name="gerar-csv",
        help="Executa todos os geradores de CSV registrados no projeto.",
        handler=handle_gerar_csv,
        configure_parser=_configurar_gerar_csv,
    ),
    CliCommand(
        name="extrair-legislaturas",
        help="Extrai os deputados vinculados às legislaturas.",
        handler=handle_extrair_legislaturas,
    ),
    CliCommand(
        name="baixar-legislaturas",
        help="Baixa o arquivo base com IDs de legislaturas.",
        handler=handle_baixar_legislaturas,
    ),
    CliCommand(
        name="extrair-dependentes",
        help="Extrai dados dependentes (ex: despesas).",
        handler=handle_extrair_dependentes,
        configure_parser=_configurar_extrair_dependentes,
    ),
    CliCommand(
        name="rodar-pipeline",
        help="Executa o pipeline completo da Câmara.",
        handler=handle_rodar_pipeline,
        configure_parser=_configurar_rodar_pipeline,
    ),
    CliCommand(
        name="portal-construir-fornecedores",
        help=(
            "Constrói a dimensão de fornecedores para enriquecimento com o "
            "Portal da Transparência."
        ),
        handler=handle_portal_construir_fornecedores,
        configure_parser=_configurar_min_ocorrencias,
    ),
    CliCommand(
        name="extrair-portal-documentos",
        help="Extrai documentos por favorecido do Portal da Transparência.",
        handler=handle_extrair_portal_documentos,
        configure_parser=_configurar_portal_documentos,
    ),
    CliCommand(
        name="extrair-portal-sancoes",
        help="Extrai CEIS, CNEP e CEPIM para os fornecedores encontrados no projeto.",
        handler=handle_extrair_portal_sancoes,
        configure_parser=_configurar_portal_simples,
    ),
    CliCommand(
        name="extrair-portal-notas-fiscais",
        help="Extrai notas fiscais do Portal da Transparência por CNPJ emitente.",
        handler=handle_extrair_portal_notas_fiscais,
        configure_parser=_configurar_portal_simples,
    ),
    CliCommand(
        name="rodar-pipeline-portal",
        help="Executa a pipeline completa de enriquecimento com o Portal da Transparência.",
        handler=handle_rodar_pipeline_portal,
        configure_parser=_configurar_portal_documentos,
    ),
    CliCommand(
        name="rodar-paralelo",
        help="Executa em paralelo as extrações que não dependem umas das outras.",
        handler=handle_rodar_paralelo,
        configure_parser=_configurar_rodar_paralelo,
    ),
    CliCommand(
        name="rodar-pipeline-completo",
        help="Executa a extração completa em fases, usando a configuração do etl-config.toml.",
        handler=handle_rodar_pipeline_completo,
        configure_parser=_configurar_rodar_pipeline_completo,
    ),
    CliCommand(
        name="extrair-senado",
        help="Extrai dados do Senado Federal (ex: CEAPS).",
        handler=handle_extrair_senado,
        configure_parser=_configurar_extrair_senado,
    ),
    CliCommand(
        name="extrair-siop",
        help="Extrai dados orçamentários do endpoint SPARQL do SIOP.",
        handler=handle_extrair_siop,
    ),
    CliCommand(
        name="extrair-ibge-localidades",
        help="Extrai regiões, estados e municípios da API de localidades do IBGE.",
        handler=handle_extrair_ibge_localidades,
        configure_parser=_configurar_extrair_ibge,
    ),
    CliCommand(
        name="extrair-pncp",
        help="Extrai contratos, atas e PCA da API pública do PNCP.",
        handler=handle_extrair_pncp,
        configure_parser=_configurar_extrair_pncp,
    ),
    _criar_comando_transferegov(
        nome="extrair-transferegov-especial",
        grupo="especial",
        help="Extrai datasets da API de Transferências Especiais do Transferegov.",
    ),
    _criar_comando_transferegov(
        nome="extrair-transferegov-fundo",
        grupo="fundoafundo",
        help="Extrai datasets da API Fundo a Fundo do Transferegov.",
    ),
    _criar_comando_transferegov(
        nome="extrair-transferegov-ted",
        grupo="ted",
        help="Extrai datasets da API TED do Transferegov.",
    ),
    CliCommand(
        name="extrair-obrasgov",
        help="Extrai projetos e execuções da API do ObrasGov.",
        handler=handle_extrair_obrasgov,
        configure_parser=_configurar_extrair_obrasgov,
    ),
    CliCommand(
        name="extrair-obrasgov-geometrias",
        help="Extrai geometrias no ObrasGov para os projetos já persistidos.",
        handler=handle_extrair_obrasgov_geometrias,
        configure_parser=_configurar_extrair_obrasgov_geometrias,
    ),
    CliCommand(
        name="extrair-siconfi",
        help="Extrai recursos da API de dados abertos do Siconfi.",
        handler=handle_extrair_siconfi,
        configure_parser=_configurar_extrair_siconfi,
    ),
    CliCommand(
        name="extrair-anp",
        help="Extrai revendedores autorizados da ANP para os CNPJs do projeto.",
        handler=handle_extrair_anp,
        configure_parser=_configurar_extrair_anp,
    ),
)

HANDLERS: dict[str, CommandHandler] = {
    nome: comando.handler
    for comando in COMMANDS
    for nome in (comando.name, *comando.aliases)
}


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

    for comando in COMMANDS:
        kwargs = {"help": comando.help}
        if comando.aliases:
            kwargs["aliases"] = list(comando.aliases)
        parser_comando = subparsers.add_parser(comando.name, **kwargs)
        if comando.configure_parser is not None:
            comando.configure_parser(parser_comando)

    return parser


def run_command(args: argparse.Namespace):
    """Despacha o comando selecionado para o handler correspondente."""

    HANDLERS[args.comando](args)


def main(argv: list[str] | None = None):
    """Inicializa a CLI, interpreta argumentos e executa o comando selecionado."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        run_command(args)
    except UserInputError as exc:
        logger.error("%s", exc)
        sys.exit(2)
    except Exception:
        logger.exception("A execução falhou:")
        sys.exit(1)


__all__ = [
    "COMMANDS",
    "HANDLERS",
    "build_parser",
    "handle_baixar_legislaturas",
    "handle_extrair_anp",
    "handle_extrair_dependentes",
    "handle_extrair_ibge_localidades",
    "handle_extrair_legislaturas",
    "handle_extrair_obrasgov",
    "handle_extrair_obrasgov_geometrias",
    "handle_extrair_pncp",
    "handle_extrair_portal_documentos",
    "handle_extrair_portal_notas_fiscais",
    "handle_extrair_portal_sancoes",
    "handle_extrair_senado",
    "handle_extrair_siconfi",
    "handle_extrair_siop",
    "handle_gerar_csv",
    "handle_menu",
    "handle_portal_construir_fornecedores",
    "handle_rodar_paralelo",
    "handle_rodar_pipeline",
    "handle_rodar_pipeline_completo",
    "handle_rodar_pipeline_portal",
    "handle_servir_cidadao_de_olho",
    "main",
    "parse_data_iso",
    "run_command",
]
