"""Extratores de sanções do Portal da Transparência."""

from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.portal.base import ExtratorPortalBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas


class ExtratorSancoesPortal(ExtratorPortalBase):
    """Consulta os datasets CEIS, CNEP e CEPIM para uma lista de documentos."""

    def __init__(self, endpoints: dict):
        """Recebe o mapeamento dataset -> endpoint e configura a concorrência."""

        super().__init__("sancoes_portal", restricted=False)
        config = obter_parametros_extrator("portal.sancoes")
        self.endpoints = endpoints
        self.max_workers = config.get("max_workers")
        self.max_pending = self.max_workers * 4
        self.stats = ContadorExecucao()

    def _incrementar(self, chave: str):
        """Atualiza contadores agregados de execução."""

        self.stats.increment(chave)

    def _relative_output_path(self, dataset: str, documento: str) -> Path:
        """Retorna o caminho relativo de saída do dataset/documento."""

        return (
            Path("portal_transparencia")
            / "sancoes"
            / dataset
            / f"fornecedor={documento}.json"
        )

    def _params_por_dataset(self, dataset: str, documento: str) -> dict | None:
        """Monta os parâmetros corretos para cada dataset de sanções."""

        if dataset in {"ceis", "cnep"}:
            return {"codigoSancionado": documento}

        if dataset == "cepim":
            if len(documento) != 14:
                return None
            return {"cnpjSancionado": documento}

        return None

    def _executar_tarefa(self, dataset: str, endpoint: str, documento: str):
        """Executa uma consulta individual de sanção para um documento."""

        params = self._params_por_dataset(dataset, documento)
        if params is None:
            self._incrementar("skipped")
            return

        try:
            resumo = self._executar_tarefa_paginada(
                endpoint=endpoint,
                base_params=params,
                relative_output_path=self._relative_output_path(dataset, documento),
                context={
                    "dataset": dataset,
                    "documento": documento,
                },
            )

            if resumo["status"] == "success":
                self._incrementar("completed")
                self.logger.info(
                    "[PORTAL] Sancoes concluido | dataset=%s | documento=%s | paginas=%s | registros=%s",
                    dataset,
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
                "[PORTAL] Falha em sancoes | dataset=%s | documento=%s",
                dataset,
                documento,
            )

    def executar(self, documentos):
        """Agenda e processa todas as consultas de sanções previstas."""

        tarefas = (
            (dataset, endpoint, documento)
            for dataset, endpoint in self.endpoints.items()
            for documento in documentos
        )
        executar_tarefas_limitadas(
            tarefas,
            self._executar_tarefa,
            max_workers=self.max_workers,
            max_pending=self.max_pending,
        )
        stats = self.stats.snapshot()

        self.logger.info(
            "[PORTAL] Sancoes finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
