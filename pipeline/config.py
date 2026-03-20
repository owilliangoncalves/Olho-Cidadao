"""Configuração declarativa dos pipelines do projeto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from configuracao import obter_configuracao_pipeline
from configuracao import obter_parametros_pipeline
from configuracao import resolver_data_configurada


def _override(valor, default):
    """Aplica override explícito sem perder valores `False` e `0`."""

    return default if valor is None else valor


@dataclass(frozen=True)
class PipelineCamaraConfig:
    """Parâmetros resolvidos do pipeline da Câmara."""

    ano_inicio: int | None
    ano_fim: int | None

    @classmethod
    def carregar(
        cls,
        *,
        ano_inicio: int | None,
        ano_fim: int | None,
    ) -> "PipelineCamaraConfig":
        config = obter_parametros_pipeline("camara")
        return cls(
            ano_inicio=_override(ano_inicio, config.get("ano_inicio")),
            ano_fim=_override(ano_fim, config.get("ano_fim")),
        )


@dataclass(frozen=True)
class PipelinePortalConfig:
    """Parâmetros resolvidos do pipeline do Portal da Transparência."""

    limit_fornecedores: int | None
    min_ocorrencias: int | None
    ano_inicio: int | None
    ano_fim: int | None
    fases: tuple[int, ...]

    @classmethod
    def carregar(
        cls,
        *,
        limit_fornecedores: int | None,
        min_ocorrencias: int | None,
        ano_inicio: int | None,
        ano_fim: int | None,
        fases: list[int] | None,
    ) -> "PipelinePortalConfig":
        config = obter_parametros_pipeline("portal")
        return cls(
            limit_fornecedores=limit_fornecedores,
            min_ocorrencias=_override(min_ocorrencias, config.get("min_ocorrencias")),
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
            fases=tuple(_override(fases, config.get("fases")) or ()),
        )


@dataclass(frozen=True)
class PipelineParaleloConfig:
    """Parâmetros resolvidos do pipeline paralelo."""

    ano_inicio: int | None
    ano_fim: int | None
    pncp_data_inicial: date | None
    pncp_data_final: date | None
    max_workers: int | None
    incluir_camara: bool | None
    incluir_senado: bool | None
    incluir_siop: bool | None
    incluir_ibge: bool | None
    incluir_pncp: bool | None
    incluir_transferegov: bool | None
    incluir_obrasgov: bool | None
    incluir_siconfi: bool | None
    senado_endpoint: str | None
    ibge_datasets: list[str] | None
    siconfi_recursos: list[str] | None
    siconfi_filtros: dict | None
    siconfi_tamanho_pagina: int | None

    @classmethod
    def carregar(
        cls,
        *,
        ano_inicio: int | None,
        ano_fim: int | None,
        pncp_data_inicial,
        pncp_data_final,
        max_workers: int | None,
        incluir_camara: bool | None,
        incluir_senado: bool | None,
        incluir_siop: bool | None,
        incluir_ibge: bool | None,
        incluir_pncp: bool | None,
        incluir_transferegov: bool | None,
        incluir_obrasgov: bool | None,
        incluir_siconfi: bool | None,
        senado_endpoint: str | None = None,
        ibge_datasets: list[str] | None = None,
        siconfi_recursos: list[str] | None = None,
        siconfi_filtros: dict | None = None,
        siconfi_tamanho_pagina: int | None = None,
    ) -> "PipelineParaleloConfig":
        config = obter_parametros_pipeline("paralelo")
        fontes = config.get("fontes", {})
        return cls(
            ano_inicio=_override(ano_inicio, config.get("ano_inicio")),
            ano_fim=_override(ano_fim, config.get("ano_fim")),
            pncp_data_inicial=_override(
                pncp_data_inicial,
                resolver_data_configurada(config.get("pncp_data_inicial")),
            ),
            pncp_data_final=_override(
                pncp_data_final,
                resolver_data_configurada(config.get("pncp_data_final")),
            ),
            max_workers=_override(max_workers, config.get("max_workers")),
            incluir_camara=_override(incluir_camara, fontes.get("camara")),
            incluir_senado=_override(incluir_senado, fontes.get("senado")),
            incluir_siop=_override(incluir_siop, fontes.get("siop")),
            incluir_ibge=_override(incluir_ibge, fontes.get("ibge")),
            incluir_pncp=_override(incluir_pncp, fontes.get("pncp")),
            incluir_transferegov=_override(incluir_transferegov, fontes.get("transferegov")),
            incluir_obrasgov=_override(incluir_obrasgov, fontes.get("obrasgov")),
            incluir_siconfi=_override(incluir_siconfi, fontes.get("siconfi")),
            senado_endpoint=_override(senado_endpoint, config.get("senado_endpoint")),
            ibge_datasets=_override(ibge_datasets, config.get("ibge_datasets")),
            siconfi_recursos=_override(siconfi_recursos, config.get("siconfi_recursos")),
            siconfi_filtros=_override(siconfi_filtros, config.get("siconfi_filtros")),
            siconfi_tamanho_pagina=_override(
                siconfi_tamanho_pagina,
                config.get("siconfi_tamanho_pagina"),
            ),
        )


@dataclass(frozen=True)
class PipelineCompletoConfig:
    """Parâmetros resolvidos do pipeline completo."""

    ano_inicio: int | None
    ano_fim: int | None
    max_workers: int | None
    incluir_camara: bool | None
    incluir_senado: bool | None
    incluir_siop: bool | None
    incluir_ibge: bool | None
    incluir_pncp: bool | None
    incluir_transferegov: bool | None
    incluir_obrasgov: bool | None
    incluir_siconfi: bool | None
    incluir_portal: bool | None
    incluir_anp: bool | None
    incluir_obrasgov_geometrias: bool | None
    pncp_data_inicial: date | None
    pncp_data_final: date | None
    senado_endpoint: str | None
    ibge_datasets: list[str] | None
    siconfi_recursos: list[str] | None
    siconfi_filtros: dict | None
    siconfi_tamanho_pagina: int | None
    portal_min_ocorrencias: int | None
    portal_limit_fornecedores: int | None
    portal_ano_inicio: int | None
    portal_ano_fim: int | None
    portal_fases: list[int] | None
    anp_min_ocorrencias: int | None
    anp_limit_fornecedores: int | None
    anp_datasets: list[str] | None
    obrasgov_geometrias_limit_ids: int | None

    @classmethod
    def carregar(
        cls,
        *,
        ano_inicio: int | None,
        ano_fim: int | None,
        max_workers: int | None,
        incluir_portal: bool | None,
        incluir_anp: bool | None,
        incluir_obrasgov_geometrias: bool | None,
    ) -> "PipelineCompletoConfig":
        config = obter_configuracao_pipeline("completo")
        fontes = config.get("fontes", {})
        portal = config.get("portal", {})
        anp = config.get("anp", {})
        pncp = config.get("pncp", {})
        senado = config.get("senado", {})
        ibge = config.get("ibge", {})
        siconfi = config.get("siconfi", {})
        obrasgov_geometrias = config.get("obrasgov_geometrias", {})

        ano_inicio_resolvido = _override(ano_inicio, config.get("ano_inicio"))
        ano_fim_resolvido = _override(ano_fim, config.get("ano_fim"))
        portal_min_ocorrencias = portal.get("min_ocorrencias")

        return cls(
            ano_inicio=ano_inicio_resolvido,
            ano_fim=ano_fim_resolvido,
            max_workers=_override(max_workers, config.get("max_workers")),
            incluir_camara=fontes.get("camara"),
            incluir_senado=fontes.get("senado"),
            incluir_siop=fontes.get("siop"),
            incluir_ibge=fontes.get("ibge"),
            incluir_pncp=fontes.get("pncp"),
            incluir_transferegov=fontes.get("transferegov"),
            incluir_obrasgov=fontes.get("obrasgov"),
            incluir_siconfi=fontes.get("siconfi"),
            incluir_portal=_override(incluir_portal, fontes.get("portal")),
            incluir_anp=_override(incluir_anp, fontes.get("anp")),
            incluir_obrasgov_geometrias=_override(
                incluir_obrasgov_geometrias,
                fontes.get("obrasgov_geometrias"),
            ),
            pncp_data_inicial=resolver_data_configurada(pncp.get("data_inicial")),
            pncp_data_final=resolver_data_configurada(pncp.get("data_final")),
            senado_endpoint=senado.get("endpoint"),
            ibge_datasets=ibge.get("datasets"),
            siconfi_recursos=siconfi.get("recursos"),
            siconfi_filtros=siconfi.get("filtros"),
            siconfi_tamanho_pagina=siconfi.get("tamanho_pagina"),
            portal_min_ocorrencias=portal_min_ocorrencias,
            portal_limit_fornecedores=portal.get("limit_fornecedores"),
            portal_ano_inicio=portal.get("ano_inicio", ano_inicio_resolvido),
            portal_ano_fim=portal.get("ano_fim", ano_fim_resolvido),
            portal_fases=portal.get("fases"),
            anp_min_ocorrencias=anp.get("min_ocorrencias", portal_min_ocorrencias),
            anp_limit_fornecedores=anp.get("limit_fornecedores"),
            anp_datasets=anp.get("datasets"),
            obrasgov_geometrias_limit_ids=obrasgov_geometrias.get("limit_ids"),
        )
