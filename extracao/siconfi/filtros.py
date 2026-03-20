"""Normalizacao e validacao de filtros do Siconfi."""

from __future__ import annotations

from infra.errors import UserInputError

from extracao.siconfi.specs import SICONFI_RESOURCES
from extracao.siconfi.specs import SICONFI_RESOURCE_SPECS
from extracao.siconfi.specs import SiconfiResourceSpec


def obter_spec_siconfi(recurso: str) -> SiconfiResourceSpec:
    """Retorna a especificacao declarativa de um recurso suportado."""

    try:
        return SICONFI_RESOURCE_SPECS[recurso]
    except KeyError as exc:
        raise UserInputError(
            f"Recurso Siconfi invalido '{recurso}'. "
            f"Use um dos recursos suportados: {', '.join(sorted(SICONFI_RESOURCES))}."
        ) from exc


def _normalizar_chave_filtro(spec: SiconfiResourceSpec, chave: str) -> str:
    """Resolve aliases de filtros para o nome canonico aceito pela API."""

    aliases = spec.aliases or {}
    return aliases.get(chave, chave)


def _normalizar_valor_filtro(chave: str, valor):
    """Ajusta caixa e formato de filtros com enum conhecido."""

    if not isinstance(valor, str):
        return valor

    valor = valor.strip()
    if chave in {
        "co_tipo_matriz",
        "co_tipo_demonstrativo",
        "in_periodicidade",
        "co_esfera",
        "co_poder",
    }:
        return valor.upper()
    if chave == "id_tv":
        return valor.lower()
    return valor


def normalizar_filtros_recurso(recurso: str, filtros: dict | None) -> dict:
    """Converte aliases e garante consistencia entre chaves equivalentes."""

    spec = obter_spec_siconfi(recurso)
    normalizados: dict = {}

    for chave, valor in (filtros or {}).items():
        chave_normalizada = _normalizar_chave_filtro(spec, chave)
        valor_normalizado = _normalizar_valor_filtro(chave_normalizada, valor)

        if (
            chave_normalizada in normalizados
            and normalizados[chave_normalizada] != valor_normalizado
        ):
            raise UserInputError(
                f"Filtros conflitantes para o recurso '{recurso}': "
                f"'{chave_normalizada}' recebeu valores diferentes "
                f"({normalizados[chave_normalizada]!r} e {valor_normalizado!r})."
            )

        normalizados[chave_normalizada] = valor_normalizado

    return normalizados


def validar_filtros_recurso(recurso: str, filtros: dict):
    """Falha cedo quando a combinacao de filtros nao atende ao contrato minimo."""

    spec = obter_spec_siconfi(recurso)
    faltantes = [chave for chave in spec.required_filters if chave not in filtros]
    if faltantes:
        exemplo = ""
        if spec.example_filters:
            exemplo = " Exemplo: " + " ".join(f"--filtro {filtro}" for filtro in spec.example_filters)
        raise UserInputError(
            f"O recurso Siconfi '{recurso}' exige os filtros obrigatorios: "
            f"{', '.join(spec.required_filters)}. "
            f"Faltando: {', '.join(faltantes)}.{exemplo}"
        )

    allowed_values = spec.allowed_values or {}
    for chave, valores_permitidos in allowed_values.items():
        if chave not in filtros:
            continue
        if filtros[chave] not in valores_permitidos:
            raise UserInputError(
                f"Filtro invalido para o recurso '{recurso}': "
                f"{chave}={filtros[chave]!r}. "
                f"Valores aceitos: {', '.join(map(str, sorted(valores_permitidos)))}."
            )

    classe_conta = filtros.get("classe_conta")
    if classe_conta is not None:
        classes_por_recurso = {
            "msc_orcamentaria": {5, 6},
            "msc_controle": {7, 8},
            "msc_patrimonial": {1, 2, 3, 4},
        }
        valores_permitidos = classes_por_recurso.get(recurso)
        if valores_permitidos and classe_conta not in valores_permitidos:
            raise UserInputError(
                f"Filtro invalido para o recurso '{recurso}': "
                f"classe_conta={classe_conta!r}. "
                f"Valores aceitos: {', '.join(map(str, sorted(valores_permitidos)))}."
            )

    mes_referencia = filtros.get("me_referencia")
    if mes_referencia is not None and not 1 <= int(mes_referencia) <= 12:
        raise UserInputError(
            "Filtro invalido para o Siconfi: me_referencia deve estar entre 1 e 12."
        )
