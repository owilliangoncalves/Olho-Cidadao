"""Configuracao e constantes do pacote Portal da Transparencia."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from configuracao import obter_parametros_extrator

PORTAL_OUTPUT_ROOT = Path("portal_transparencia")
PORTAL_STATE_ROOT = Path("data/_estado/portal")
PORTAL_FORNECEDORES_PATH = Path("data/portal_transparencia/dimensoes/fornecedores.jsonl")


@dataclass(frozen=True)
class PortalAPIConfig:
    restricted_limit_rpm: int
    day_limit_rpm: int
    night_limit_rpm: int
    timezone: str

    @classmethod
    def carregar(cls) -> "PortalAPIConfig":
        config = obter_parametros_extrator("portal.api")
        return cls(
            restricted_limit_rpm=int(config.get("restricted_limit_rpm") or 1),
            day_limit_rpm=int(config.get("day_limit_rpm") or 1),
            night_limit_rpm=int(config.get("night_limit_rpm") or 1),
            timezone=config.get("timezone") or "America/Sao_Paulo",
        )


@dataclass(frozen=True)
class PortalExecucaoConfig:
    max_workers: int

    @property
    def max_pending(self) -> int:
        """Deriva a fila local maxima a partir do paralelismo."""

        return self.max_workers * 4

    @classmethod
    def carregar(cls, nome_extrator: str) -> "PortalExecucaoConfig":
        config = obter_parametros_extrator(nome_extrator)
        return cls(max_workers=max(1, int(config.get("max_workers") or 1)))


@dataclass(frozen=True)
class PortalFornecedoresConfig:
    min_ocorrencias: int

    @classmethod
    def carregar(
        cls,
        *,
        min_ocorrencias: int | None = None,
    ) -> "PortalFornecedoresConfig":
        config = obter_parametros_extrator("portal.fornecedores")
        return cls(
            min_ocorrencias=max(
                1,
                int(
                    min_ocorrencias
                    if min_ocorrencias is not None
                    else config.get("min_ocorrencias") or 1
                ),
            )
        )
