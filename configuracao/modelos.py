"""Modelos tipados que representam o schema de configuração do projeto."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EndpointConfig:
    endpoint: str
    depende_de: str | None = None
    itens: int = 500
    campo_id: str = "id"
    salvar_como: str | None = None
    paginacao: bool = False
    ano_inicio: int | None = None
    ano_fim: int | None = None
    restricted: bool | None = None
    fases: list[int] = field(default_factory=list)


@dataclass(slots=True)
class PipelineConfig:
    etapas: list[str] = field(default_factory=list)
    descricao: str | None = None
    ano_inicio: int | None = None
    ano_fim: int | None = None
    max_workers: int | None = None
    fontes: dict[str, bool] = field(default_factory=dict)
    portal: dict[str, Any] = field(default_factory=dict)
    senado: dict[str, Any] = field(default_factory=dict)
    ibge: dict[str, Any] = field(default_factory=dict)
    pncp: dict[str, Any] = field(default_factory=dict)
    siconfi: dict[str, Any] = field(default_factory=dict)
    anp: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConfigOperacional:
    cli: dict[str, dict[str, Any]] = field(default_factory=dict)
    extratores: dict[str, dict[str, Any]] = field(default_factory=dict)
    pipelines: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(slots=True)
class ProjetoConfig:
    endpoints: dict[str, EndpointConfig] = field(default_factory=dict)
    pipelines: dict[str, PipelineConfig] = field(default_factory=dict)
    config: ConfigOperacional = field(default_factory=ConfigOperacional)
