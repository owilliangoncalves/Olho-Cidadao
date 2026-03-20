"""Fachada pública e orquestração do pacote de pipelines do projeto."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from configuracao import obter_configuracao_endpoint
from configuracao.logger import logger
from extracao.anp import RevendedoresANP
from extracao.camara.deputados_federais import DeputadosLegislatura
from extracao.camara.deputados_federais import Despesas
from extracao.camara.deputados_federais import Legislatura
from extracao.ibge import LocalidadesIBGE
from extracao.obrasgov import ObrasGov
from extracao.pncp import PNCPConsulta
from extracao.portal import ConstrutorDimFornecedoresPortal
from extracao.portal import ExtratorDocumentosPorFavorecidoPortal
from extracao.portal import ExtratorNotasFiscaisPortal
from extracao.portal import ExtratorSancoesPortal
from extracao.portal.tarefas import gerar_tarefas_documentos
from extracao.senado import DadosSenado
from extracao.siconfi import Siconfi
from extracao.siop import SIOP
from extracao.transferegov import TransferegovRecursos
from pipeline.config import PipelineCamaraConfig
from pipeline.config import PipelineCompletoConfig
from pipeline.config import PipelineParaleloConfig
from pipeline.config import PipelinePortalConfig
from pipeline.tarefas import TarefaParalela
from pipeline.tarefas import documentos_fornecedores
from pipeline.tarefas import portal_api_key_configurada
from pipeline.tarefas import validar_intervalo_anos
from pipeline.tarefas import validar_intervalo_datas
from pipeline.tarefas import validar_max_workers
from utils.csv.despesas_deputados import ConversorDespesasCSV
from infra.errors import UserInputError


def _expor_config(instancia, cfg) -> None:
    """Espelha os campos da config na instância para uso interno simples."""

    instancia.cfg = cfg
    instancia.__dict__.update(vars(cfg))


class PipelineCamara:
    """Executa a cadeia completa de extração e consolidação da Câmara."""

    def __init__(self, ano_inicio: int | None = None, ano_fim: int | None = None):
        _expor_config(
            self,
            PipelineCamaraConfig.carregar(ano_inicio=ano_inicio, ano_fim=ano_fim),
        )

    def _validar_precondicoes(self):
        """Falha cedo quando a configuração anual da Câmara é inválida."""

        validar_intervalo_anos(
            self.ano_inicio,
            self.ano_fim,
            contexto="da Camara",
            required=True,
        )

    def executar(self):
        """Executa todas as etapas do pipeline da Câmara em sequência."""

        logger.info("=== INICIANDO PIPELINE COMPLETO DA CÂMARA ===")
        self._validar_precondicoes()

        logger.info("--- Etapa 0: Extraindo lista de legislaturas ---")
        Legislatura().executar()

        logger.info("--- Etapa 1: Extraindo deputados por legislatura ---")
        DeputadosLegislatura().executar()

        logger.info(
            "--- Etapa 2: Extraindo despesas (%s a %s) ---",
            self.ano_inicio,
            self.ano_fim - 1,
        )
        endpoint_despesas = "deputados_despesas"
        config_despesas = obter_configuracao_endpoint(endpoint_despesas)
        Despesas(endpoint_despesas, config_despesas).executar(
            ano_inicio=self.ano_inicio,
            ano_fim=self.ano_fim,
        )

        logger.info("--- Etapa 3: Consolidando despesas em CSV ---")
        ConversorDespesasCSV().executar()

        logger.info("=== PIPELINE FINALIZADO COM SUCESSO ===")


class PipelinePortalTransparencia:
    """Coordena a dimensão local de fornecedores e seus enriquecimentos."""

    def __init__(
        self,
        limit_fornecedores: int | None = None,
        min_ocorrencias: int | None = None,
        ano_inicio: int | None = None,
        ano_fim: int | None = None,
        fases: list[int] | None = None,
    ):
        _expor_config(
            self,
            PipelinePortalConfig.carregar(
                limit_fornecedores=limit_fornecedores,
                min_ocorrencias=min_ocorrencias,
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                fases=fases,
            ),
        )
        self.builder = ConstrutorDimFornecedoresPortal()
        validar_intervalo_anos(
            self.ano_inicio,
            self.ano_fim,
            contexto="do Portal",
            required=False,
        )

    @staticmethod
    def _endpoint_portal(nome: str) -> str:
        """Resolve o path configurado para um endpoint do Portal."""

        return obter_configuracao_endpoint(nome)["endpoint"]

    def _validar_fases_documentos(self):
        """Garante que a configuração de fases é válida para documentos."""

        if not self.fases:
            raise UserInputError(
                "O pipeline do Portal exige ao menos uma fase em "
                "[config.pipelines.portal].fases ou via --fases."
            )

        if any(not isinstance(fase, int) or fase <= 0 for fase in self.fases):
            raise UserInputError(
                "As fases do pipeline do Portal devem ser inteiros positivos."
            )

    def _carregar_fornecedores(self):
        """Constrói e carrega a dimensão de fornecedores a ser enriquecida."""

        self.builder.construir(min_ocorrencias=self.min_ocorrencias)
        fornecedores = self.builder.carregar()
        if self.limit_fornecedores is not None:
            return fornecedores[: self.limit_fornecedores]
        return fornecedores

    def executar_dimensao(self):
        """Reconstrói a dimensão local de fornecedores."""

        return self.builder.construir(min_ocorrencias=self.min_ocorrencias)

    def executar_documentos(self):
        """Extrai o detalhamento de documentos por favorecido."""

        self._validar_fases_documentos()
        tarefas = gerar_tarefas_documentos(
            self._carregar_fornecedores(),
            list(self.fases),
            ano_inicio=self.ano_inicio,
            ano_fim=self.ano_fim,
        )
        if not tarefas:
            logger.warning("[PORTAL] Nenhuma tarefa de documentos por favorecido foi gerada.")
            return

        ExtratorDocumentosPorFavorecidoPortal(
            self._endpoint_portal("portal_documentos_favorecido")
        ).executar(tarefas)

    def executar_sancoes(self):
        """Consulta CEIS, CNEP e CEPIM para os fornecedores selecionados."""

        documentos = documentos_fornecedores(self._carregar_fornecedores())
        if not documentos:
            logger.warning("[PORTAL] Nenhum fornecedor disponivel para extrair sancoes.")
            return

        ExtratorSancoesPortal(
            {
                "ceis": self._endpoint_portal("portal_ceis"),
                "cnep": self._endpoint_portal("portal_cnep"),
                "cepim": self._endpoint_portal("portal_cepim"),
            }
        ).executar(documentos)

    def executar_notas_fiscais(self):
        """Consulta notas fiscais emitidas pelos fornecedores selecionados."""

        documentos = documentos_fornecedores(self._carregar_fornecedores())
        if not documentos:
            logger.warning("[PORTAL] Nenhum fornecedor disponivel para extrair notas fiscais.")
            return

        ExtratorNotasFiscaisPortal(
            self._endpoint_portal("portal_notas_fiscais")
        ).executar(documentos)

    def executar(self):
        """Executa todas as etapas do pipeline do Portal da Transparência."""

        logger.info("=== INICIANDO PIPELINE DO PORTAL DA TRANSPARENCIA ===")
        self.executar_dimensao()
        self.executar_documentos()
        self.executar_sancoes()
        self.executar_notas_fiscais()
        logger.info("=== PIPELINE DO PORTAL DA TRANSPARENCIA FINALIZADO ===")


class PipelineParalelo:
    """Executa em paralelo os extratores que não conflitam entre si."""

    def __init__(
        self,
        ano_inicio: int | None = None,
        ano_fim: int | None = None,
        pncp_data_inicial=None,
        pncp_data_final=None,
        max_workers: int | None = None,
        incluir_camara: bool | None = None,
        incluir_senado: bool | None = None,
        incluir_siop: bool | None = None,
        incluir_ibge: bool | None = None,
        incluir_pncp: bool | None = None,
        incluir_transferegov: bool | None = None,
        incluir_obrasgov: bool | None = None,
        incluir_siconfi: bool | None = None,
        senado_endpoint: str | None = None,
        ibge_datasets: list[str] | None = None,
        siconfi_recursos: list[str] | None = None,
        siconfi_filtros: dict | None = None,
        siconfi_tamanho_pagina: int | None = None,
    ):
        _expor_config(
            self,
            PipelineParaleloConfig.carregar(
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                pncp_data_inicial=pncp_data_inicial,
                pncp_data_final=pncp_data_final,
                max_workers=max_workers,
                incluir_camara=incluir_camara,
                incluir_senado=incluir_senado,
                incluir_siop=incluir_siop,
                incluir_ibge=incluir_ibge,
                incluir_pncp=incluir_pncp,
                incluir_transferegov=incluir_transferegov,
                incluir_obrasgov=incluir_obrasgov,
                incluir_siconfi=incluir_siconfi,
                senado_endpoint=senado_endpoint,
                ibge_datasets=ibge_datasets,
                siconfi_recursos=siconfi_recursos,
                siconfi_filtros=siconfi_filtros,
                siconfi_tamanho_pagina=siconfi_tamanho_pagina,
            ),
        )
        self._validar_precondicoes()

    def _validar_precondicoes(self):
        """Falha cedo quando a configuração do pipeline paralelo é inválida."""

        validar_intervalo_anos(
            self.ano_inicio,
            self.ano_fim,
            contexto="paralelo",
            required=True,
        )
        validar_intervalo_datas(
            self.pncp_data_inicial,
            self.pncp_data_final,
            contexto="paralelo",
            campo_inicial="pncp_data_inicial",
            campo_final="pncp_data_final",
        )
        validar_max_workers(self.max_workers, contexto="paralelo")

    def _tarefas_transferegov(self) -> tuple[TarefaParalela, ...]:
        """Agrupa as três APIs do ecossistema Transferegov."""

        return (
            TarefaParalela(
                nome="transferegov_especial",
                executar=lambda: TransferegovRecursos(grupo="especial").executar(),
            ),
            TarefaParalela(
                nome="transferegov_fundoafundo",
                executar=lambda: TransferegovRecursos(grupo="fundoafundo").executar(),
            ),
            TarefaParalela(
                nome="transferegov_ted",
                executar=lambda: TransferegovRecursos(grupo="ted").executar(),
            ),
        )

    def _tarefas(self) -> list[TarefaParalela]:
        """Monta a lista de tarefas independentes a executar em paralelo."""

        tarefas: list[TarefaParalela] = []

        if self.incluir_camara:
            tarefas.append(
                TarefaParalela(
                    nome="camara",
                    executar=lambda: PipelineCamara(
                        ano_inicio=self.ano_inicio,
                        ano_fim=self.ano_fim,
                    ).executar(),
                )
            )
        if self.incluir_senado:
            tarefas.append(
                TarefaParalela(
                    nome="senado",
                    executar=lambda: DadosSenado(self.senado_endpoint).executar(),
                )
            )
        if self.incluir_siop:
            tarefas.append(TarefaParalela(nome="siop", executar=lambda: SIOP().executar()))
        if self.incluir_ibge:
            tarefas.append(
                TarefaParalela(
                    nome="ibge",
                    executar=lambda: LocalidadesIBGE().executar(datasets=self.ibge_datasets),
                )
            )
        if self.incluir_pncp:
            tarefas.append(
                TarefaParalela(
                    nome="pncp",
                    executar=lambda: PNCPConsulta().executar(
                        data_inicial=self.pncp_data_inicial,
                        data_final=self.pncp_data_final,
                    ),
                )
            )
        if self.incluir_transferegov:
            tarefas.extend(self._tarefas_transferegov())
        if self.incluir_obrasgov:
            tarefas.append(
                TarefaParalela(
                    nome="obrasgov",
                    executar=lambda: ObrasGov().executar_recursos(),
                )
            )
        if self.incluir_siconfi:
            tarefas.append(
                TarefaParalela(
                    nome="siconfi",
                    executar=lambda: Siconfi(page_size=self.siconfi_tamanho_pagina).executar(
                        recursos=self.siconfi_recursos,
                        filtros=self.siconfi_filtros,
                    ),
                )
            )

        return tarefas

    def executar(self):
        """Executa o conjunto de tarefas com paralelismo limitado por módulo."""

        tarefas = self._tarefas()
        if not tarefas:
            logger.warning("[PARALELO] Nenhuma tarefa selecionada para execucao.")
            return

        concluidas: list[str] = []
        falhas: list[str] = []
        limite = min(self.max_workers, len(tarefas))

        logger.info(
            "[PARALELO] Iniciando execucao | tarefas=%s | max_workers=%s",
            [tarefa.nome for tarefa in tarefas],
            limite,
        )

        with ThreadPoolExecutor(max_workers=limite) as executor:
            futuros = {
                executor.submit(tarefa.executar): tarefa.nome
                for tarefa in tarefas
            }
            for futuro in as_completed(futuros):
                nome = futuros[futuro]
                try:
                    futuro.result()
                except Exception:
                    falhas.append(nome)
                    logger.exception("[PARALELO] Tarefa falhou | tarefa=%s", nome)
                else:
                    concluidas.append(nome)
                    logger.info("[PARALELO] Tarefa concluida | tarefa=%s", nome)

        logger.info(
            "[PARALELO] Execucao finalizada | concluidas=%s | falhas=%s",
            concluidas,
            falhas,
        )
        if falhas:
            raise RuntimeError(
                "Falha em uma ou mais tarefas do pipeline paralelo: "
                + ", ".join(sorted(falhas))
            )


class PipelineCompleto:
    """Executa a extração completa em fases sem hard code de parâmetros."""

    def __init__(
        self,
        ano_inicio: int | None = None,
        ano_fim: int | None = None,
        max_workers: int | None = None,
        incluir_portal: bool | None = None,
        incluir_anp: bool | None = None,
        incluir_obrasgov_geometrias: bool | None = None,
    ):
        _expor_config(
            self,
            PipelineCompletoConfig.carregar(
                ano_inicio=ano_inicio,
                ano_fim=ano_fim,
                max_workers=max_workers,
                incluir_portal=incluir_portal,
                incluir_anp=incluir_anp,
                incluir_obrasgov_geometrias=incluir_obrasgov_geometrias,
            ),
        )

    def _validar_precondicoes(self):
        """Falha cedo quando a configuração do pipeline é inválida."""

        validar_intervalo_anos(
            self.ano_inicio,
            self.ano_fim,
            contexto="completo",
            required=True,
        )
        validar_max_workers(self.max_workers, contexto="completo")
        if self.incluir_portal and not portal_api_key_configurada():
            raise UserInputError(
                "O pipeline completo inclui o Portal da Transparencia, mas nenhuma chave "
                "de API foi encontrada. Defina PORTAL_TRANSPARENCIA_API_KEY "
                "ou rode com --sem-portal."
            )

    def executar(self):
        """Executa o pipeline completo em duas fases."""

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
            RevendedoresANP(
                min_ocorrencias=self.anp_min_ocorrencias,
                limit_fornecedores=self.anp_limit_fornecedores,
            ).executar(datasets=self.anp_datasets)

        if self.incluir_obrasgov_geometrias:
            logger.info("=== FASE DEPENDENTE: OBRASGOV GEOMETRIAS ===")
            ObrasGov().executar_geometrias(limit_ids=self.obrasgov_geometrias_limit_ids)

        logger.info("=== PIPELINE COMPLETO FINALIZADO ===")


__all__ = [
    "PipelineCamara",
    "PipelineCompleto",
    "PipelineParalelo",
    "PipelinePortalTransparencia",
]
