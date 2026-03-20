"""Helpers puros usados pela orquestração do pacote SIOP."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

_PADRAO_ANO = re.compile(r"(?:orcamento_item_despesa_|ano=)(\d{4})")


def agora_iso() -> str:
    """Retorna o timestamp UTC usado nos checkpoints do SIOP."""

    return datetime.now(timezone.utc).isoformat()


def anos_locais(base_dir: Path, state_dir: Path) -> list[int]:
    """Infere os anos já tocados a partir de saídas e checkpoints locais."""

    anos: set[int] = set()

    for diretorio in (base_dir, state_dir):
        if not diretorio.exists():
            continue

        for caminho in (*diretorio.glob("*.json*"), *diretorio.glob("ano=*/")):
            match = _PADRAO_ANO.search(str(caminho))
            if match:
                anos.add(int(match.group(1)))

    return sorted(anos, reverse=True)


def anos_priorizados(anos_conhecidos: Iterable[int], ano_atual: int | None = None) -> list[int]:
    """Prioriza ano fechado, ano corrente e depois o backlog histórico."""

    ano_base = datetime.now().year if ano_atual is None else ano_atual
    ano_fechado = ano_base - 1
    fila = [ano_fechado, ano_base, *anos_conhecidos, *range(ano_base - 2, 2009, -1)]

    ordenados: list[int] = []
    vistos: set[int] = set()

    for ano in fila:
        if ano < 2010 or ano in vistos:
            continue
        vistos.add(ano)
        ordenados.append(ano)

    return ordenados
