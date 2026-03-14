"""Orquestra uma execução completa e configurável do projeto."""

from __future__ import annotations

import os

from configuracao.endpoint import obter_configuracao_pipeline
from configuracao.logger import logger
from configuracao.projeto import resolver_data_configurada
from extracao.anp.revendedores import ExtratorRevendedoresANP
from extracao.obrasgov.obras import ExtratorObrasGov
from infra.errors import UserInputError
from pipeline_paralelo import PipelineParalelo
from pipeline_portal import PipelinePortalTransparencia


class PipelineCompleto:
    """Executa a extração completa em fases sem hard code de parâmetros.

    A configuração é lida da seção `[pipelines.completo]` em `etl-config.toml`.
    A CLI pode sobrescrever apenas os parâmetros mais usados, mantendo a
    configuração operacional versionada no repositório.
    """

    def __init__(
        self,
        ano_inicio: int | None = None,
        ano_fim: int | None = None,
        max_workers: int | None = None,
        incluir_portal: bool | None = None,
        incluir_anp: bool | None = None,
        incluir_obrasgov_geometrias: bool | None = None,
    ):
        """Lê a configuração do pipeline e aplica overrides explícitos."""

        config = obter_configuracao_pipeline("completo")
        fontes = config.get("fontes", {})
        portal = config.get("portal", {})
        anp = config.get("anp", {})
        pncp = config.get("pncp", {})
        senado = config.get("senado", {})
        ibge = config.get("ibge", {})
        siconfi = config.get("siconfi", {})
        obrasgov_geometrias = config.get("obrasgov_geometrias", {})

        self.ano_inicio = ano_inicio if ano_inicio is not None else config.get("ano_inicio")
        self.ano_fim = ano_fim if ano_fim is not None else config.get("ano_fim")
        self.max_workers = max_workers if max_workers is not None else config.get("max_workers")

        self.incluir_camara = fontes.get("camara")
        self.incluir_senado = fontes.get("senado")
        self.incluir_siop = fontes.get("siop")
        self.incluir_ibge = fontes.get("ibge")
        self.incluir_pncp = fontes.get("pncp")
        self.incluir_transferegov = fontes.get("transferegov")
        self.incluir_obrasgov = fontes.get("obrasgov")
        self.incluir_siconfi = fontes.get("siconfi")
        self.incluir_portal = (
            incluir_portal if incluir_portal is not None else fontes.get("portal")
        )
        self.incluir_anp = (
            incluir_anp if incluir_anp is not None else fontes.get("anp")
        )
        self.incluir_obrasgov_geometrias = (
            incluir_obrasgov_geometrias
            if incluir_obrasgov_geometrias is not None
            else fontes.get("obrasgov_geometrias")
        )

        self.pncp_data_inicial = resolver_data_configurada(pncp.get("data_inicial"))
        self.pncp_data_final = resolver_data_configurada(pncp.get("data_final"))
        self.senado_endpoint = senado.get("endpoint")
        self.ibge_datasets = ibge.get("datasets")
        self.siconfi_recursos = siconfi.get("recursos")
        self.siconfi_filtros = siconfi.get("filtros")
        self.siconfi_tamanho_pagina = siconfi.get("tamanho_pagina")

        self.portal_min_ocorrencias = portal.get("min_ocorrencias")
        self.portal_limit_fornecedores = portal.get("limit_fornecedores")
        self.portal_ano_inicio = portal.get("ano_inicio", self.ano_inicio)
        self.portal_ano_fim = portal.get("ano_fim", self.ano_fim)
        self.portal_fases = portal.get("fases")

        self.anp_min_ocorrencias = anp.get("min_ocorrencias", self.portal_min_ocorrencias)
        self.anp_limit_fornecedores = anp.get("limit_fornecedores")
        self.anp_datasets = anp.get("datasets")

        self.obrasgov_geometrias_limit_ids = obrasgov_geometrias.get("limit_ids")

    def _validar_precondicoes(self):
        """Falha cedo quando a configuração do pipeline é inválida."""

        if self.ano_inicio is None or self.ano_fim is None:
            raise UserInputError(
                "O pipeline completo exige ano_inicio e ano_fim. "
                "Defina [pipelines.completo] no etl-config.toml "
                "ou informe --ano-inicio/--ano-fim."
            )

        if self.ano_inicio >= self.ano_fim:
            raise UserInputError("ano_inicio deve ser menor que ano_fim no pipeline completo.")

        if self.max_workers is None:
            raise UserInputError(
                "O pipeline completo exige max_workers. "
                "Defina [pipelines.completo].max_workers no etl-config.toml "
                "ou informe --max-workers."
            )

        if self.max_workers < 1:
            raise UserInputError("max_workers deve ser maior ou igual a 1.")

        if self.incluir_portal and not (
            os.getenv("PORTAL_TRANSPARENCIA_API_KEY")
            or os.getenv("CHAVE_API_DADOS")
        ):
            raise UserInputError(
                "O pipeline completo inclui o Portal da Transparencia, mas nenhuma chave "
                "de API foi encontrada. Defina PORTAL_TRANSPARENCIA_API_KEY "
                "ou rode com --sem-portal."
            )

    def executar(self):
        """Executa o pipeline completo em duas fases.

        Fase 1:
        fontes independentes ou que já possuem sua própria orquestração.

        Fase 2:
        enriquecimentos que dependem de saídas já existentes, como Portal,
        ANP e geometrias do ObrasGov.
        """

        logger.info("=== INICIANDO PIPELINE COMPLETO ===")
        self._validar_precondicoes()

        PipelineParalelo(
            ano_inicio=self.ano_inicio,
            ano_fim=self.ano_fim,
            pncp_data_inicial=self.pncp_data_inicial,
            pncp_data_final=self.pncp_data_final,
            max_workers=self.max_workers,
            incluir_camara=self.incluir_camara,
            incluir_senado=self.incluir_senado,
            incluir_siop=self.incluir_siop,
            incluir_ibge=self.incluir_ibge,
            incluir_pncp=self.incluir_pncp,
            incluir_transferegov=self.incluir_transferegov,
            incluir_obrasgov=self.incluir_obrasgov,
            incluir_siconfi=self.incluir_siconfi,
            senado_endpoint=self.senado_endpoint,
            ibge_datasets=self.ibge_datasets,
            siconfi_recursos=self.siconfi_recursos,
            siconfi_filtros=self.siconfi_filtros,
            siconfi_tamanho_pagina=self.siconfi_tamanho_pagina,
        ).executar()

        if self.incluir_portal:
            logger.info("=== FASE DEPENDENTE: PORTAL DA TRANSPARENCIA ===")
            PipelinePortalTransparencia(
                limit_fornecedores=self.portal_limit_fornecedores,
                min_ocorrencias=self.portal_min_ocorrencias,
                ano_inicio=self.portal_ano_inicio,
                ano_fim=self.portal_ano_fim,
                fases=self.portal_fases,
            ).executar()

        if self.incluir_anp:
            logger.info("=== FASE DEPENDENTE: ANP ===")
            ExtratorRevendedoresANP(
                min_ocorrencias=self.anp_min_ocorrencias,
                limit_fornecedores=self.anp_limit_fornecedores,
            ).executar(datasets=self.anp_datasets)

        if self.incluir_obrasgov_geometrias:
            logger.info("=== FASE DEPENDENTE: OBRASGOV GEOMETRIAS ===")
            ExtratorObrasGov().executar_geometrias(
                limit_ids=self.obrasgov_geometrias_limit_ids
            )

        logger.info("=== PIPELINE COMPLETO FINALIZADO ===")
