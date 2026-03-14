"""Extrator do endpoint restrito de documentos por favorecido do Portal."""

from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.portal.base import ExtratorPortalBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas


class ExtratorDocumentosPorFavorecidoPortal(ExtratorPortalBase):
    """Extrai documentos por favorecido para combinações de documento/ano/fase."""

    def __init__(self, endpoint: str):
        """Configura o endpoint restrito e o nível de concorrência adotado."""

        super().__init__("documentos_por_favorecido", restricted=True)
        config = obter_parametros_extrator("portal.documentos")
        self.endpoint = endpoint
        self.max_workers = config.get("max_workers")
        self.max_pending = self.max_workers * 4
        self.stats = ContadorExecucao()

    def _incrementar(self, chave: str):
        """Atualiza as estatísticas de execução de forma thread-safe."""

        self.stats.increment(chave)

    def _relative_output_path(self, documento: str, ano: int, fase: int) -> Path:
        """Retorna o caminho relativo de saída da combinação consultada."""

        return (
            Path("portal_transparencia")
            / "documentos_por_favorecido"
            / f"ano={ano}"
            / f"fase={fase}"
            / f"fornecedor={documento}.json"
        )

    def _executar_tarefa(self, documento: str, ano: int, fase: int):
        """Executa uma tarefa individual do endpoint de documentos."""

        try:
            resumo = self._executar_tarefa_paginada(
                endpoint=self.endpoint,
                base_params={
                    "codigoPessoa": documento,
                    "fase": fase,
                    "ano": ano,
                },
                relative_output_path=self._relative_output_path(documento, ano, fase),
                context={
                    "documento": documento,
                    "ano": ano,
                    "fase": fase,
                },
            )

            if resumo["status"] == "success":
                self._incrementar("completed")
                self.logger.info(
                    "[PORTAL] Documentos favorecido concluido | documento=%s | ano=%s | fase=%s | paginas=%s | registros=%s",
                    documento,
                    ano,
                    fase,
                    resumo["pages"],
                    resumo["records"],
                )
            elif resumo["status"] in {"skipped", "skipped_empty"}:
                self._incrementar("skipped")
            else:
                self._incrementar("empty")
        except Exception:
            self._incrementar("failed")
            self.logger.exception(
                "[PORTAL] Falha em documentos por favorecido | documento=%s | ano=%s | fase=%s",
                documento,
                ano,
                fase,
            )

    def executar(self, tarefas):
        """Processa a fila de tarefas com concorrência limitada."""

        executar_tarefas_limitadas(
            tarefas,
            self._executar_tarefa,
            max_workers=self.max_workers,
            max_pending=self.max_pending,
        )
        stats = self.stats.snapshot()

        self.logger.info(
            "[PORTAL] Documentos por favorecido finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
