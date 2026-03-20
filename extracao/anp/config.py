"""Configuracao e constantes do extrator de revendedores da ANP."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_parametros_extrator

ANP_DATASETS = {
    "combustivel": "/v1/combustivel",
    "glp": "/v1/glp",
}

ANP_PAGINACAO = {
    "style": "page",
    "page_param": "numeropagina",
    "start_page": 1,
}


@dataclass(frozen=True)
class RevendedoresConfig:
    min_ocorrencias: int | None
    limit_fornecedores: int | None
    max_workers: int
    datasets: tuple[str, ...]
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @property
    def max_pending(self) -> int:
        """Deriva a fila máxima a partir do paralelismo configurado."""

        return self.max_workers * 4

    @classmethod
    def carregar(
        cls,
        *,
        min_ocorrencias: int | None,
        limit_fornecedores: int | None,
    ) -> "RevendedoresConfig":
        config = obter_parametros_extrator("anp")
        max_workers = int(config.get("max_workers") or 1)
        return cls(
            min_ocorrencias=(
                min_ocorrencias
                if min_ocorrencias is not None
                else config.get("min_ocorrencias")
            ),
            limit_fornecedores=limit_fornecedores,
            max_workers=max_workers,
            datasets=tuple(config.get("datasets") or ANP_DATASETS.keys()),
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
