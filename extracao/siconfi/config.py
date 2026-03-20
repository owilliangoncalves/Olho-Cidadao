"""Configuracao e constantes do pacote Siconfi."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_parametros_extrator

SICONFI_PAGINACAO = {
    "style": "offset",
    "offset_param": "offset",
    "limit_param": "limit",
    "start_offset": 0,
}


@dataclass(frozen=True)
class SiconfiConfig:
    page_size: int | None
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @classmethod
    def carregar(cls, *, page_size: int | None) -> "SiconfiConfig":
        """Carrega defaults do projeto e aplica overrides locais."""

        config = obter_parametros_extrator("siconfi")
        return cls(
            page_size=page_size if page_size is not None else config.get("page_size"),
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
