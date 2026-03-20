"""Especificacoes declarativas dos recursos suportados pelo Siconfi."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SiconfiResourceSpec:
    """Define o contrato minimo de um recurso do Siconfi."""

    path: str
    required_filters: tuple[str, ...] = ()
    aliases: dict[str, str] | None = None
    allowed_values: dict[str, frozenset] | None = None
    example_filters: tuple[str, ...] = ()


COMMON_ALIASES = {
    "cod_ibge": "id_ente",
    "ano": "an_referencia",
    "ano_referencia": "an_referencia",
    "ano_exercicio": "an_exercicio",
    "mes": "me_referencia",
    "mes_referencia": "me_referencia",
    "tipo_matriz": "co_tipo_matriz",
    "tipo_valor": "id_tv",
}

SICONFI_RESOURCE_SPECS = {
    "entes": SiconfiResourceSpec(
        path="/entes",
        aliases={"cod_ibge": "id_ente"},
        example_filters=(),
    ),
    "extrato_entregas": SiconfiResourceSpec(
        path="/extrato_entregas",
        required_filters=("id_ente", "an_referencia"),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        example_filters=("id_ente=3550308", "an_referencia=2024"),
    ),
    "msc_orcamentaria": SiconfiResourceSpec(
        path="/msc_orcamentaria",
        required_filters=(
            "id_ente",
            "an_referencia",
            "me_referencia",
            "co_tipo_matriz",
            "classe_conta",
            "id_tv",
        ),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        allowed_values={
            "co_tipo_matriz": frozenset({"MSCC", "MSCE"}),
            "id_tv": frozenset({"beginning_balance", "ending_balance", "period_change"}),
        },
        example_filters=(
            "id_ente=3550308",
            "an_referencia=2024",
            "me_referencia=12",
            "co_tipo_matriz=MSCC",
            "classe_conta=6",
            "id_tv=period_change",
        ),
    ),
    "msc_controle": SiconfiResourceSpec(
        path="/msc_controle",
        required_filters=(
            "id_ente",
            "an_referencia",
            "me_referencia",
            "co_tipo_matriz",
            "classe_conta",
            "id_tv",
        ),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        allowed_values={
            "co_tipo_matriz": frozenset({"MSCC", "MSCE"}),
            "id_tv": frozenset({"beginning_balance", "ending_balance", "period_change"}),
        },
        example_filters=(
            "id_ente=3550308",
            "an_referencia=2024",
            "me_referencia=12",
            "co_tipo_matriz=MSCC",
            "classe_conta=8",
            "id_tv=period_change",
        ),
    ),
    "msc_patrimonial": SiconfiResourceSpec(
        path="/msc_patrimonial",
        required_filters=(
            "id_ente",
            "an_referencia",
            "me_referencia",
            "co_tipo_matriz",
            "classe_conta",
            "id_tv",
        ),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        allowed_values={
            "co_tipo_matriz": frozenset({"MSCC", "MSCE"}),
            "id_tv": frozenset({"beginning_balance", "ending_balance", "period_change"}),
        },
        example_filters=(
            "id_ente=3550308",
            "an_referencia=2024",
            "me_referencia=12",
            "co_tipo_matriz=MSCC",
            "classe_conta=1",
            "id_tv=period_change",
        ),
    ),
    "rreo": SiconfiResourceSpec(
        path="/rreo",
        required_filters=(
            "an_exercicio",
            "nr_periodo",
            "co_tipo_demonstrativo",
            "id_ente",
        ),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_exercicio",
        },
        example_filters=(
            "an_exercicio=2024",
            "nr_periodo=6",
            "co_tipo_demonstrativo=RREO",
            "id_ente=3550308",
        ),
    ),
    "rgf": SiconfiResourceSpec(
        path="/rgf",
        required_filters=(
            "an_exercicio",
            "in_periodicidade",
            "nr_periodo",
            "co_tipo_demonstrativo",
            "co_poder",
            "id_ente",
        ),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_exercicio",
            "periodicidade": "in_periodicidade",
            "poder": "co_poder",
            "esfera": "co_esfera",
        },
        allowed_values={
            "in_periodicidade": frozenset({"S", "Q"}),
        },
        example_filters=(
            "an_exercicio=2024",
            "in_periodicidade=Q",
            "nr_periodo=3",
            "co_tipo_demonstrativo=RGF",
            "co_poder=E",
            "id_ente=3550308",
        ),
    ),
    "dca": SiconfiResourceSpec(
        path="/dca",
        required_filters=("an_exercicio", "id_ente"),
        aliases={
            **COMMON_ALIASES,
            "exercicio": "an_exercicio",
        },
        example_filters=("an_exercicio=2024", "id_ente=3550308"),
    ),
}

SICONFI_RESOURCES = {
    nome_recurso: spec.path for nome_recurso, spec in SICONFI_RESOURCE_SPECS.items()
}
