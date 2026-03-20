"""Helpers puros para o pacote do PNCP."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from datetime import timedelta
from pathlib import Path


def fim_do_mes(inicio: date) -> date:
    """Retorna a data final do mês da data informada."""

    proximo_mes = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
    return proximo_mes - timedelta(days=1)


def iterar_janelas_mensais(data_inicial: date, data_final: date) -> Iterator[tuple[date, date]]:
    """Divide um intervalo de datas em janelas mensais fechadas."""

    cursor = data_inicial.replace(day=1)
    while cursor <= data_final:
        inicio = max(cursor, data_inicial)
        fim = min(fim_do_mes(cursor), data_final)
        yield inicio, fim
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)


def iterar_anos(data_inicial: date, data_final: date) -> range:
    """Retorna o intervalo anual fechado coberto pelas datas informadas."""

    return range(data_inicial.year, data_final.year + 1)


def output_path_janela(resource: str, inicio: date) -> Path:
    """Retorna o caminho relativo de saída de uma janela mensal."""

    return Path("pncp") / resource / f"ano={inicio.year}" / f"mes={inicio.month:02d}.json"


def output_path_pca(ano: int) -> Path:
    """Retorna o caminho relativo de saída do PCA anual."""

    return Path("pncp") / "pca" / f"ano={ano}.json"
