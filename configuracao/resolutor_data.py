"""Responsabilidade única: resolver valores de data em diferentes formatos."""

from __future__ import annotations

from datetime import date


def resolver_data_configurada(valor: date | str | None) -> date | None:
    """Resolve um valor de data em qualquer formato para date."""
    if valor is None or valor == "":
        return None

    if isinstance(valor, date):
        return valor

    token = str(valor).strip()
    if token == "today":
        return date.today()
    if token == "start_of_current_year":
        return date.today().replace(month=1, day=1)

    return date.fromisoformat(token)


def resolver_data_configurada_iso(valor: date | str | None) -> str | None:
    """Resolve um valor de data e retorna em formato ISO."""
    resolvida = resolver_data_configurada(valor)
    return resolvida.isoformat() if resolvida else None
