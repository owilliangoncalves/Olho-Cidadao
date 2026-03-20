"""Configuração do pacote de localidades do IBGE."""

from __future__ import annotations

from dataclasses import dataclass

IBGE_DATASETS = {
    "regioes": "/api/v1/localidades/regioes",
    "estados": "/api/v1/localidades/estados",
    "municipios": "/api/v1/localidades/municipios",
}


@dataclass(frozen=True)
class LocalidadesIBGEConfig:
    """Configuração operacional do extrator de localidades."""

    datasets: tuple[str, ...]
    rate_limit_per_sec: float
    max_rate_per_sec: float

    @classmethod
    def carregar(cls) -> "LocalidadesIBGEConfig":
        """Retorna a configuração estável do pacote."""

        return cls(
            datasets=tuple(IBGE_DATASETS),
            rate_limit_per_sec=3.0,
            max_rate_per_sec=6.0,
        )
