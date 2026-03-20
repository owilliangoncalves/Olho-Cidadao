"""Configuracao do extrator de despesas CEAPS do Senado."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_configuracao_endpoint
from infra.errors import UserInputError


@dataclass(frozen=True)
class SenadoConfig:
    """Representa a configuracao resolvida para uma extracao do Senado."""

    nome_endpoint: str
    endpoint: str
    ano_inicio: int
    ano_fim: int

    @classmethod
    def carregar(cls, nome_endpoint: str) -> "SenadoConfig":
        """Resolve e valida a configuracao declarativa do endpoint."""

        config = obter_configuracao_endpoint(nome_endpoint)
        ano_inicio = int(config["ano_inicio"])
        ano_fim = int(config["ano_fim"])
        if ano_inicio > ano_fim:
            raise UserInputError(
                "ano_inicio nao pode ser maior que ano_fim na configuracao do Senado."
            )
        return cls(
            nome_endpoint=nome_endpoint,
            endpoint=config["endpoint"],
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
