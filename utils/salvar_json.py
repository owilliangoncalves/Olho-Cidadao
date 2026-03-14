"""Persistência incremental de objetos JSON em formato JSON Lines."""

import json
from pathlib import Path


def salvar_json_incremental(nome_arquivo: str, dados, append=True):
    """Escreve um ou mais registros JSON no arquivo de destino.

    Args:
        nome_arquivo: Caminho relativo ao diretório `data/`.
        dados: Dicionário único ou iterável de dicionários a serem gravados.
        append: Quando verdadeiro, concatena ao arquivo existente.

    Returns:
        Caminho final do arquivo salvo.
    """

    Path("data").mkdir(exist_ok=True)

    caminho = Path("data") / nome_arquivo
    caminho.parent.mkdir(parents=True, exist_ok=True)

    modo = "a" if append and caminho.exists() else "w"

    with open(caminho, modo, encoding="utf-8") as f:
        if isinstance(dados, dict):
            json.dump(dados, f, ensure_ascii=False)
            f.write("\n")

        else:
            for registro in dados:
                json.dump(registro, f, ensure_ascii=False)
                f.write("\n")

    return caminho
