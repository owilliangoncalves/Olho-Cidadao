"""Helpers para leitura leve de arquivos JSON Lines."""

import json
from pathlib import Path


def primeiro_registro_jsonl(caminho: Path) -> dict | None:
    """Retorna o primeiro objeto JSON válido de um arquivo JSON Lines."""

    if not caminho.exists() or caminho.stat().st_size == 0:
        return None

    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            try:
                return json.loads(linha)
            except json.JSONDecodeError:
                return None

    return None


def arquivo_jsonl_tem_chaves(caminho: Path, chaves: set[str]) -> bool:
    """Indica se o primeiro registro válido contém todas as chaves esperadas."""

    registro = primeiro_registro_jsonl(caminho)
    if not registro:
        return False
    return chaves.issubset(registro.keys())


def arquivo_jsonl_meta_tem_chaves(caminho: Path, chaves: set[str]) -> bool:
    """Indica se `_meta` do primeiro registro possui as chaves esperadas."""

    registro = primeiro_registro_jsonl(caminho)
    if not registro:
        return False

    meta = registro.get("_meta", {})
    if not isinstance(meta, dict):
        return False

    return chaves.issubset(meta.keys())


def contar_registros_jsonl(caminho: Path) -> int:
    """Conta as linhas não vazias de um arquivo JSON Lines.

    O helper é usado para reconciliar checkpoints com o conteúdo efetivamente
    persistido em arquivos temporários durante retomadas de escrita.
    """

    if not caminho.exists() or caminho.stat().st_size == 0:
        return 0

    total = 0
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                total += 1
    return total
