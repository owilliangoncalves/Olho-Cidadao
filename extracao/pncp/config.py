"""Configuração do pacote de consultas públicas do PNCP."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_parametros_extrator

MONTHLY_RESOURCES = {
    "contratos": "pncp_contratos",
    "atas": "pncp_atas",
}

PNCP_PAGINACAO = {
    "style": "page",
    "page_param": "pagina",
    "page_size_param": "tamanhoPagina",
    "start_page": 1,
}


@dataclass(frozen=True)
class PNCPConsultaConfig:
    """Configuração operacional do extrator PNCP."""

    page_size: int
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @classmethod
    def carregar(cls, page_size: int | None = None) -> "PNCPConsultaConfig":
        """Lê e normaliza a configuração operacional do PNCP."""

        config = obter_parametros_extrator("pncp")
        resolved_page_size = page_size if page_size is not None else config.get("page_size")
        return cls(
            page_size=max(10, int(resolved_page_size or 10)),
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
