"""Configuracao e constantes do extrator do ObrasGov."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_parametros_extrator

PAGEABLE_RESOURCES = {
    "projeto-investimento": "/projeto-investimento",
    "execucao-fisica": "/execucao-fisica",
    "execucao-financeira": "/execucao-financeira",
}

OBRASGOV_PAGINACAO = {
    "style": "page",
    "page_param": "pagina",
    "page_size_param": "tamanhoDaPagina",
    "start_page": 1,
}


@dataclass(frozen=True)
class ObrasGovConfig:
    page_size: int | None
    max_workers: int
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @property
    def max_pending(self) -> int:
        """Deriva a fila máxima local a partir do paralelismo."""

        return self.max_workers * 4

    @classmethod
    def carregar(cls, *, page_size: int | None) -> "ObrasGovConfig":
        config = obter_parametros_extrator("obrasgov")
        max_workers = int(config.get("max_workers") or 1)
        return cls(
            page_size=page_size if page_size is not None else config.get("page_size"),
            max_workers=max_workers,
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
