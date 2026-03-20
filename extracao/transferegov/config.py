"""Configuração e catálogos do pacote Transferegov."""

from __future__ import annotations

from dataclasses import dataclass

from configuracao import obter_parametros_extrator
from infra.errors import UserInputError

RESOURCE_GROUPS = {
    "especial": (
        "programa_especial",
        "plano_acao_especial",
        "executor_especial",
        "empenho_especial",
        "ordem_pagamento_ordem_bancaria_especial",
        "historico_pagamento_especial",
    ),
    "fundoafundo": (
        "programa",
        "plano_acao",
        "empenho",
        "relatorio_gestao",
    ),
    "ted": (
        "programa",
        "plano_acao",
        "termo_execucao",
        "nota_credito",
        "programacao_financeira",
        "trf",
    ),
}

ORGAO_MAP = {
    "especial": "transferegov_especial",
    "fundoafundo": "transferegov_fundoafundo",
    "ted": "transferegov_ted",
}

TRANSFEREGOV_PAGINACAO = {
    "style": "offset",
    "offset_param": "offset",
    "limit_param": "limit",
    "start_offset": 0,
}


def validar_grupo_transferegov(grupo: str) -> str:
    """Garante que o grupo solicitado exista no catálogo público."""

    if grupo not in RESOURCE_GROUPS:
        raise UserInputError(
            f"Grupo Transferegov desconhecido: {grupo}. "
            f"Use um dos grupos: {', '.join(sorted(RESOURCE_GROUPS))}."
        )
    return grupo


@dataclass(frozen=True)
class TransferegovConfig:
    """Parâmetros operacionais compartilhados pelo pacote."""

    grupo: str
    page_size: int | None
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @classmethod
    def carregar(
        cls,
        *,
        grupo: str,
        page_size: int | None,
    ) -> "TransferegovConfig":
        """Carrega defaults do projeto e aplica overrides locais."""

        config = obter_parametros_extrator("transferegov")
        return cls(
            grupo=validar_grupo_transferegov(grupo),
            page_size=page_size if page_size is not None else config.get("page_size"),
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
