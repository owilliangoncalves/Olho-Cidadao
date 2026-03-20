"""Pacote ANP com fachada pública e orquestração concentradas aqui.

Responsabilidades:
- expor a configuração e os helpers públicos do pacote;
- construir o orquestrador `RevendedoresANP` sob demanda;
- manter a importação do pacote leve para não acoplar a CLI à pilha HTTP.
"""

from __future__ import annotations

from functools import cache
from typing import Any

from extracao.anp.config import ANP_DATASETS
from extracao.anp.config import ANP_PAGINACAO
from extracao.anp.config import RevendedoresConfig
from extracao.anp.documentos import carregar_documentos_revendedores
from extracao.anp.tarefas import contador_por_status
from extracao.anp.tarefas import iterar_tarefas_revendedores
from extracao.anp.tarefas import output_path_revendedor

def executar_tarefas_limitadas(*args, **kwargs):
    """Importa o executor concorrente apenas quando a ANP é executada."""

    from infra.concorrencia import executar_tarefas_limitadas as executar

    return executar(*args, **kwargs)


@cache
def _construir_revendedores_anp():
    """Cria e memoriza a classe do orquestrador para manter o pacote leve."""

    from extracao.portal import ConstrutorDimFornecedoresPortal
    from extracao.publica import ExtratorAPIPublicaBase
    from infra.concorrencia import ContadorExecucao

    class RevendedoresANP(ExtratorAPIPublicaBase):
        """Consulta a ANP para verificar revendedores por CNPJ."""

        def __init__(
            self,
            min_ocorrencias: int | None = None,
            limit_fornecedores: int | None = None,
        ):
            """Configura o crawler com a dimensão local de fornecedores como seed."""

            self.cfg = RevendedoresConfig.carregar(
                min_ocorrencias=min_ocorrencias,
                limit_fornecedores=limit_fornecedores,
            )
            super().__init__(
                orgao="anp",
                nome_endpoint="revendedores",
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )
            self.builder = ConstrutorDimFornecedoresPortal()
            self.stats = ContadorExecucao()

        def _carregar_documentos(self) -> list[str]:
            """Carrega CNPJs da dimensão consolidada de fornecedores."""

            return carregar_documentos_revendedores(
                builder=self.builder,
                min_ocorrencias=self.cfg.min_ocorrencias,
                limit_fornecedores=self.cfg.limit_fornecedores,
            )

        def _executar_tarefa(self, dataset: str, documento: str):
            """Executa a consulta de um CNPJ em um dataset da ANP."""

            endpoint = ANP_DATASETS.get(dataset)
            if endpoint is None:
                self.logger.warning("[ANP] Dataset desconhecido, pulando | dataset=%s", dataset)
                self.stats.increment("skipped")
                return

            try:
                resumo = self._executar_tarefa_paginada(
                    endpoint=endpoint,
                    base_params={"cnpj": documento},
                    relative_output_path=output_path_revendedor(dataset, documento),
                    context={"dataset": dataset, "documento": documento},
                    pagination=ANP_PAGINACAO,
                    item_keys=("data",),
                    _allow_empty_retry=False,
                    _persist_empty_marker=False,
                )
                self.stats.increment(contador_por_status(resumo.get("status")))
            except Exception:
                self.stats.increment("failed")
                self.logger.exception(
                    "[ANP] Falha em revendedores | dataset=%s | documento=%s",
                    dataset,
                    documento,
                )

        def executar(self, datasets: list[str] | None = None):
            """Agenda a extração dos datasets da ANP para os CNPJs conhecidos."""

            datasets_selecionados = tuple(datasets or self.cfg.datasets)
            documentos = self._carregar_documentos()

            if not documentos:
                self.logger.warning("[ANP] Nenhum fornecedor disponível para consulta.")
                return

            self.logger.info(
                "[ANP] Iniciando revendedores | datasets=%s | documentos=%s",
                datasets_selecionados,
                len(documentos),
            )

            executar_tarefas_limitadas(
                iterar_tarefas_revendedores(datasets_selecionados, documentos),
                self._executar_tarefa,
                max_workers=self.cfg.max_workers,
                max_pending=self.cfg.max_pending,
            )

            stats = self.stats.snapshot()
            self.logger.info(
                "[ANP] Revendedores finalizado | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
                stats["completed"],
                stats["skipped"],
                stats["empty"],
                stats["failed"],
            )

    RevendedoresANP.__module__ = __name__
    return RevendedoresANP


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "RevendedoresANP":
        revendedores = _construir_revendedores_anp()
        globals()[name] = revendedores
        return revendedores
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantém introspecção consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "ANP_DATASETS",
    "ANP_PAGINACAO",
    "RevendedoresANP",
    "RevendedoresConfig",
    "carregar_documentos_revendedores",
]
