"""Pacote Portal com fachada publica e orquestracao concentradas aqui."""

from __future__ import annotations

from functools import cache
from typing import Any

from extracao.portal.config import PortalExecucaoConfig
from extracao.portal.fornecedores import ConstrutorDimFornecedoresPortal
from extracao.portal.tarefas import contador_por_status
from extracao.portal.tarefas import documento_tem_cnpj
from extracao.portal.tarefas import iterar_tarefas_sancoes
from extracao.portal.tarefas import output_path_documentos
from extracao.portal.tarefas import output_path_notas_fiscais
from extracao.portal.tarefas import output_path_sancao
from extracao.portal.tarefas import params_sancao


def executar_tarefas_limitadas(*args, **kwargs):
    """Importa o executor concorrente apenas quando necessario."""

    from infra.concorrencia import executar_tarefas_limitadas as executar

    return executar(*args, **kwargs)


@cache
def _construir_extrator_documentos():
    """Cria e memoriza o extrator publico de documentos por favorecido."""

    from extracao.portal.base import ExtratorPortalBase
    from infra.concorrencia import ContadorExecucao

    class ExtratorDocumentosPorFavorecidoPortal(ExtratorPortalBase):
        """Extrai documentos por favorecido para combinacoes documento/ano/fase."""

        def __init__(self, endpoint: str):
            self.cfg = PortalExecucaoConfig.carregar("portal.documentos")
            self.endpoint = endpoint
            super().__init__("documentos_por_favorecido", restricted=True)
            self.stats = ContadorExecucao()

        def _executar_tarefa(self, documento: str, ano: int, fase: int):
            """Executa uma tarefa individual do endpoint de documentos."""

            try:
                resumo = self._executar_tarefa_paginada(
                    endpoint=self.endpoint,
                    base_params={"codigoPessoa": documento, "fase": fase, "ano": ano},
                    relative_output_path=output_path_documentos(documento, ano, fase),
                    context={"documento": documento, "ano": ano, "fase": fase},
                )
                self.stats.increment(contador_por_status(resumo.get("status")))
                if resumo["status"] == "success":
                    self.logger.info(
                        "[PORTAL] Documentos favorecido concluido | documento=%s | ano=%s | fase=%s | paginas=%s | registros=%s",
                        documento,
                        ano,
                        fase,
                        resumo["pages"],
                        resumo["records"],
                    )
            except Exception:
                self.stats.increment("failed")
                self.logger.exception(
                    "[PORTAL] Falha em documentos por favorecido | documento=%s | ano=%s | fase=%s",
                    documento,
                    ano,
                    fase,
                )

        def executar(self, tarefas):
            """Processa a fila de tarefas com concorrencia limitada."""

            enviados = executar_tarefas_limitadas(
                tarefas,
                self._executar_tarefa,
                max_workers=self.cfg.max_workers,
                max_pending=self.cfg.max_pending,
            )
            if enviados == 0:
                self.logger.warning(
                    "[PORTAL] Nenhuma tarefa de documentos por favorecido foi agendada."
                )
                return

            stats = self.stats.snapshot()
            self.logger.info(
                "[PORTAL] Documentos por favorecido finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
                stats["completed"],
                stats["skipped"],
                stats["empty"],
                stats["failed"],
            )

    ExtratorDocumentosPorFavorecidoPortal.__module__ = __name__
    return ExtratorDocumentosPorFavorecidoPortal


@cache
def _construir_extrator_notas_fiscais():
    """Cria e memoriza o extrator publico de notas fiscais."""

    from extracao.portal.base import ExtratorPortalBase
    from infra.concorrencia import ContadorExecucao

    class ExtratorNotasFiscaisPortal(ExtratorPortalBase):
        """Consulta notas fiscais emitidas por fornecedores com CNPJ conhecido."""

        def __init__(self, endpoint: str):
            self.cfg = PortalExecucaoConfig.carregar("portal.notas_fiscais")
            self.endpoint = endpoint
            super().__init__("notas_fiscais_portal", restricted=False)
            self.stats = ContadorExecucao()

        def _executar_tarefa(self, documento: str):
            """Executa a consulta de notas fiscais para um documento."""

            if not documento_tem_cnpj(documento):
                self.stats.increment("skipped")
                return

            try:
                resumo = self._executar_tarefa_paginada(
                    endpoint=self.endpoint,
                    base_params={"cnpjEmitente": documento},
                    relative_output_path=output_path_notas_fiscais(documento),
                    context={"documento": documento},
                )
                self.stats.increment(contador_por_status(resumo.get("status")))
                if resumo["status"] == "success":
                    self.logger.info(
                        "[PORTAL] Notas fiscais concluido | documento=%s | paginas=%s | registros=%s",
                        documento,
                        resumo["pages"],
                        resumo["records"],
                    )
            except Exception:
                self.stats.increment("failed")
                self.logger.exception("[PORTAL] Falha em notas fiscais | documento=%s", documento)

        def executar(self, documentos):
            """Processa todas as consultas de notas fiscais agendadas."""

            enviados = executar_tarefas_limitadas(
                documentos,
                self._executar_tarefa,
                max_workers=self.cfg.max_workers,
                max_pending=self.cfg.max_pending,
            )
            if enviados == 0:
                self.logger.warning("[PORTAL] Nenhuma tarefa de notas fiscais foi agendada.")
                return

            stats = self.stats.snapshot()
            self.logger.info(
                "[PORTAL] Notas fiscais finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
                stats["completed"],
                stats["skipped"],
                stats["empty"],
                stats["failed"],
            )

    ExtratorNotasFiscaisPortal.__module__ = __name__
    return ExtratorNotasFiscaisPortal


@cache
def _construir_extrator_sancoes():
    """Cria e memoriza o extrator publico de sancoes."""

    from extracao.portal.base import ExtratorPortalBase
    from infra.concorrencia import ContadorExecucao

    class ExtratorSancoesPortal(ExtratorPortalBase):
        """Consulta os datasets CEIS, CNEP e CEPIM para uma lista de documentos."""

        def __init__(self, endpoints: dict[str, str]):
            self.cfg = PortalExecucaoConfig.carregar("portal.sancoes")
            self.endpoints = endpoints
            super().__init__("sancoes_portal", restricted=False)
            self.stats = ContadorExecucao()

        def _executar_tarefa(self, dataset: str, endpoint: str, documento: str):
            """Executa uma consulta individual de sancao para um documento."""

            params = params_sancao(dataset, documento)
            if params is None:
                self.stats.increment("skipped")
                return

            try:
                resumo = self._executar_tarefa_paginada(
                    endpoint=endpoint,
                    base_params=params,
                    relative_output_path=output_path_sancao(dataset, documento),
                    context={"dataset": dataset, "documento": documento},
                )
                self.stats.increment(contador_por_status(resumo.get("status")))
                if resumo["status"] == "success":
                    self.logger.info(
                        "[PORTAL] Sancoes concluido | dataset=%s | documento=%s | paginas=%s | registros=%s",
                        dataset,
                        documento,
                        resumo["pages"],
                        resumo["records"],
                    )
            except Exception:
                self.stats.increment("failed")
                self.logger.exception(
                    "[PORTAL] Falha em sancoes | dataset=%s | documento=%s",
                    dataset,
                    documento,
                )

        def executar(self, documentos):
            """Agenda e processa todas as consultas de sancoes previstas."""

            enviados = executar_tarefas_limitadas(
                iterar_tarefas_sancoes(self.endpoints, documentos),
                self._executar_tarefa,
                max_workers=self.cfg.max_workers,
                max_pending=self.cfg.max_pending,
            )
            if enviados == 0:
                self.logger.warning("[PORTAL] Nenhuma tarefa de sancoes foi agendada.")
                return

            stats = self.stats.snapshot()
            self.logger.info(
                "[PORTAL] Sancoes finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
                stats["completed"],
                stats["skipped"],
                stats["empty"],
                stats["failed"],
            )

    ExtratorSancoesPortal.__module__ = __name__
    return ExtratorSancoesPortal


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "ExtratorDocumentosPorFavorecidoPortal":
        extrator = _construir_extrator_documentos()
        globals()[name] = extrator
        return extrator
    if name == "ExtratorNotasFiscaisPortal":
        extrator = _construir_extrator_notas_fiscais()
        globals()[name] = extrator
        return extrator
    if name == "ExtratorSancoesPortal":
        extrator = _construir_extrator_sancoes()
        globals()[name] = extrator
        return extrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantem introspeccao consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "ConstrutorDimFornecedoresPortal",
    "ExtratorDocumentosPorFavorecidoPortal",
    "ExtratorNotasFiscaisPortal",
    "ExtratorSancoesPortal",
]
