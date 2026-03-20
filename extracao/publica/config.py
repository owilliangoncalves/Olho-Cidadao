"""Configuracao compartilhada da base de APIs publicas."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_parametros_extrator


@dataclass(frozen=True)
class PublicaBaseConfig:
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @classmethod
    def carregar(
        cls,
        *,
        rate_limit_per_sec: float | None,
        max_rate_per_sec: float | None,
    ) -> "PublicaBaseConfig":
        defaults = obter_parametros_extrator("publica")
        return cls(
            rate_limit_per_sec=(
                rate_limit_per_sec
                if rate_limit_per_sec is not None
                else defaults.get("rate_limit_per_sec")
            ),
            max_rate_per_sec=(
                max_rate_per_sec
                if max_rate_per_sec is not None
                else defaults.get("max_rate_per_sec")
            ),
        )
