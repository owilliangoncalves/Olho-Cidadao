from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(slots=True)
class EndpointConfig:
    endpoint: str
    depende_de: str | None = None
    itens: int = 500
    campo_id: str = "id"


@dataclass(slots=True)
class PipelineConfig:
    etapas: list[str] = field(default_factory=list)
    descricao: str | None = None


@dataclass(slots=True)
class CliIntervaloAnosConfig:
    inicio: date | str | None = None
    fim: date | str | None = None


@dataclass(slots=True)
class CliConfig:
    intervalo_anos: CliIntervaloAnosConfig = field(default_factory=CliIntervaloAnosConfig)
    comandos: dict[str, dict[str, Any]] = field(default_factory=dict)


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