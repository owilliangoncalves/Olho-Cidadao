"""Helpers para navegação em APIs paginadas."""


def proxima_pagina(resposta: dict) -> str | None:
    """Extrai a URL da próxima página a partir do campo `links` da resposta."""

    for link in resposta.get("links", []):
        if link.get("rel") == "next":
            return link.get("href")
    return None
