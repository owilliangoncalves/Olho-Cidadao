"""Pacote IBGE com fachada pública e orquestração concentradas aqui."""

from __future__ import annotations

from functools import cache
from typing import Any

from extracao.ibge.config import IBGE_DATASETS
from extracao.ibge.config import LocalidadesIBGEConfig
from extracao.ibge.tarefas import output_path_localidade
from extracao.ibge.tarefas import resolver_datasets_solicitados


@cache
def _construir_localidades_ibge():
    """Cria e memoriza o orquestrador público do pacote."""

    from extracao.publica import ExtratorAPIPublicaBase

    class LocalidadesIBGE(ExtratorAPIPublicaBase):
        """Baixa dimensões territoriais do IBGE para padronização de joins."""

        def __init__(self):
            self.cfg = LocalidadesIBGEConfig.carregar()
            super().__init__(
                orgao="ibge",
                nome_endpoint="localidades",
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )

        def executar(self, datasets: list[str] | None = None):
            """Extrai os datasets de localidades solicitados."""

            selecionados, invalidos = resolver_datasets_solicitados(datasets)
            for dataset in invalidos:
                self.logger.warning("[IBGE] Dataset desconhecido, pulando | dataset=%s", dataset)

            if not selecionados:
                self.logger.warning("[IBGE] Nenhum dataset válido informado.")
                return {}

            resultados: dict[str, dict] = {}
            for dataset in selecionados:
                resumo = self._executar_tarefa_unica(
                    endpoint=IBGE_DATASETS[dataset],
                    params={},
                    relative_output_path=output_path_localidade(dataset),
                    context={"dataset": dataset},
                )
                resultados[dataset] = resumo
                self.logger.info(
                    "[IBGE] Dataset concluido | dataset=%s | status=%s | registros=%s",
                    dataset,
                    resumo["status"],
                    resumo["records"],
                )

            return resultados

    LocalidadesIBGE.__module__ = __name__
    return LocalidadesIBGE


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "LocalidadesIBGE":
        localidades = _construir_localidades_ibge()
        globals()[name] = localidades
        return localidades
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantém introspecção consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "IBGE_DATASETS",
    "LocalidadesIBGE",
    "LocalidadesIBGEConfig",
]
