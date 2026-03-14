"""Extrator do endpoint de notas fiscais do Portal da Transparência."""

from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.portal.base import ExtratorPortalBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas


class ExtratorNotasFiscaisPortal(ExtratorPortalBase):
    """Consulta notas fiscais emitidas por fornecedores com CNPJ conhecido."""

    def __init__(self, endpoint: str):
        """Configura o endpoint e a estratégia de concorrência do extrator."""

        super().__init__("notas_fiscais_portal", restricted=False)
        config = obter_parametros_extrator("portal.notas_fiscais")
        self.endpoint = endpoint
        self.max_workers = config.get("max_workers")
        self.max_pending = self.max_workers * 4
        self.stats = ContadorExecucao()

    def _incrementar(self, chave: str):
        """Atualiza estatísticas agregadas com proteção por lock."""

        self.stats.increment(chave)

    def _relative_output_path(self, documento: str) -> Path:
        """Retorna o caminho relativo de saída do fornecedor consultado."""

        return (
            Path("portal_transparencia")
            / "notas_fiscais"
            / f"fornecedor={documento}.json"
        )

    def _executar_tarefa(self, documento: str):
        """Executa a consulta de notas fiscais para um documento."""

        if len(documento) != 14:
            self._incrementar("skipped")
            return

        try:
            resumo = self._executar_tarefa_paginada(
                endpoint=self.endpoint,
                base_params={"cnpjEmitente": documento},
                relative_output_path=self._relative_output_path(documento),
                context={"documento": documento},
            )

            if resumo["status"] == "success":
                self._incrementar("completed")
                self.logger.info(
                    "[PORTAL] Notas fiscais concluido | documento=%s | paginas=%s | registros=%s",
                    documento,
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
                "[PORTAL] Falha em notas fiscais | documento=%s",
                documento,
            )

    def executar(self, documentos):
        """Processa todas as consultas de notas fiscais agendadas."""

        executar_tarefas_limitadas(
            documentos,
            self._executar_tarefa,
            max_workers=self.max_workers,
            max_pending=self.max_pending,
        )
        stats = self.stats.snapshot()

        self.logger.info(
            "[PORTAL] Notas fiscais finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
