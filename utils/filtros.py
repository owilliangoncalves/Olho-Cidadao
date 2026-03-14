"""Helpers para filtros de CLI e nomes determinísticos de consultas."""

from __future__ import annotations

import hashlib
import re

from infra.errors import UserInputError


def _coagir_valor(valor: str):
    """Converte valores textuais simples para tipos mais úteis."""

    texto = valor.strip()
    if texto.lower() == "true":
        return True
    if texto.lower() == "false":
        return False
    if texto.isdigit():
        return int(texto)

    try:
        return float(texto)
    except ValueError:
        return texto


def parse_filtros_cli(filtros: list[str] | None) -> dict:
    """Converte uma lista `chave=valor` em dicionário.

    Args:
        filtros: Lista recebida da CLI.

    Returns:
        Dicionário com valores coeridos quando possível.

    Raises:
        UserInputError: Quando algum item não segue o formato `chave=valor`.
    """

    resultado = {}
    for filtro in filtros or []:
        if "=" not in filtro:
            raise UserInputError(
                f"Filtro inválido '{filtro}'. Use o formato chave=valor."
            )

        chave, valor = filtro.split("=", 1)
        chave = chave.strip()
        if not chave:
            raise UserInputError(
                f"Filtro inválido '{filtro}'. A chave não pode ser vazia."
            )

        resultado[chave] = _coagir_valor(valor)

    return resultado


def slug_filtros(filtros: dict | None, default: str = "all") -> str:
    """Gera um identificador estável e seguro para caminhos de consulta."""

    if not filtros:
        return default

    partes = []
    for chave, valor in sorted(filtros.items()):
        chave_segura = re.sub(r"[^0-9A-Za-z_-]+", "-", str(chave)).strip("-") or "chave"
        valor_seguro = re.sub(r"[^0-9A-Za-z._-]+", "-", str(valor)).strip("-") or "vazio"
        partes.append(f"{chave_segura}={valor_seguro}")

    slug = "__".join(partes)
    if len(slug) <= 140:
        return slug

    hash_curto = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:120].rstrip('-_')}-{hash_curto}"
