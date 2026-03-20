"""Configuracao do pacote SIOP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from configuracao import obter_parametros_extrator

SIOP_OUTPUT_DIR = Path("siop")
SIOP_STATE_DIR = Path("data/_estado/siop")


@dataclass(frozen=True)
class SiopConfig:
    """Agrupa os parâmetros operacionais do extrator do SIOP."""

    funcoes_orcamentarias: tuple[str, ...]
    max_workers_particoes: int
    page_size_inicial: int
    page_size_minima: int
    detail_batch_size: int
    max_workers_detalhes: int
    max_query_length: int
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @property
    def output_dir(self) -> Path:
        """Subdiretório relativo onde o pacote grava seus artefatos."""

        return SIOP_OUTPUT_DIR

    @property
    def state_dir(self) -> Path:
        """Diretório absoluto relativo ao projeto para checkpoints locais."""

        return SIOP_STATE_DIR

    @classmethod
    def carregar(cls) -> "SiopConfig":
        """Carrega defaults do projeto e aplica o contrato do pacote."""

        config = obter_parametros_extrator("siop")
        return cls(
            funcoes_orcamentarias=tuple(config.get("funcoes_orcamentarias") or ()),
            max_workers_particoes=int(config.get("max_workers_particoes") or 6),
            page_size_inicial=int(config.get("page_size_inicial") or 400),
            page_size_minima=int(config.get("page_size_minima") or 50),
            detail_batch_size=int(config.get("detail_batch_size") or 100),
            max_workers_detalhes=int(config.get("max_workers_detalhes") or 2),
            max_query_length=int(config.get("max_query_length") or 7000),
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
