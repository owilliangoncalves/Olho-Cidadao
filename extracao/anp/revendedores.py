"""Extratores de revendedores autorizados da ANP."""

from __future__ import annotations

from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.portal.fornecedores import ConstrutorDimFornecedoresPortal
from extracao.publica.base import ExtratorAPIPublicaBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas

ANP_DATASETS = {
    "combustivel": "/v1/combustivel",
    "glp": "/v1/glp",
}


class ExtratorRevendedoresANP(ExtratorAPIPublicaBase):
    """Consulta a ANP para verificar revendedores por CNPJ."""

    def __init__(
        self,
        min_ocorrencias: int | None = None,
        limit_fornecedores: int | None = None,
    ):
        """Configura o crawler com a dimensão local de fornecedores como seed."""

        config = obter_parametros_extrator("anp")
        super().__init__(
            orgao="anp",
            nome_endpoint="revendedores",
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
        self.min_ocorrencias = (
            min_ocorrencias if min_ocorrencias is not None else config.get("min_ocorrencias")
        )
        self.limit_fornecedores = limit_fornecedores
        self.builder = ConstrutorDimFornecedoresPortal()
        self.max_workers = config.get("max_workers")
        self.max_pending = self.max_workers * 4
        self.stats = ContadorExecucao()

    def _incrementar(self, chave: str):
        """Atualiza as estatísticas do crawler."""

        self.stats.increment(chave)

    def _carregar_documentos(self):
        """Carrega CNPJs da dimensão consolidada de fornecedores."""

        self.builder.construir(min_ocorrencias=self.min_ocorrencias)
        fornecedores = self.builder.carregar()

        if self.limit_fornecedores is not None:
            fornecedores = fornecedores[: self.limit_fornecedores]

        return [
            item["documento"]
            for item in fornecedores
            if item.get("tipo_documento") == "cnpj"
        ]

    def _executar_tarefa(self, dataset: str, documento: str):
        """Executa a consulta de um CNPJ em um dataset da ANP."""

        try:
            resumo = self._executar_tarefa_paginada(
                endpoint=ANP_DATASETS[dataset],
                base_params={"cnpj": documento},
                relative_output_path=(
                    Path("anp")
                    / "revendedores"
                    / dataset
                    / f"fornecedor={documento}.json"
                ),
                context={
                    "dataset": dataset,
                    "documento": documento,
                },
                pagination={
                    "style": "page",
                    "page_param": "numeropagina",
                    "start_page": 1,
                },
                item_keys=("data",),
                _allow_empty_retry=False,
                _persist_empty_marker=False,
            )

            if resumo["status"] == "success":
                self._incrementar("completed")
            elif resumo["status"] in {"skipped", "skipped_empty"}:
                self._incrementar("skipped")
            else:
                self._incrementar("empty")
        except Exception:
            self._incrementar("failed")
            self.logger.exception(
                "[ANP] Falha em revendedores | dataset=%s | documento=%s",
                dataset,
                documento,
            )

    def executar(self, datasets: list[str] | None = None):
        """Agenda a extração dos datasets da ANP para os CNPJs conhecidos."""

        config = obter_parametros_extrator("anp")
        datasets_selecionados = datasets or config.get("datasets") or list(ANP_DATASETS)
        documentos = self._carregar_documentos()
        tarefas = (
            (dataset, documento)
            for dataset in datasets_selecionados
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
            "[ANP] Revendedores finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
