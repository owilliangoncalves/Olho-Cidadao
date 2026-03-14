"""Leitura utilitária de identificadores a partir de um arquivo JSON."""

import json
from pathlib import Path


def carregar_ids(endpoint_pai, campo_id):
    """Carrega os identificadores de um arquivo `data/<endpoint>.json`.

    Notes:
        Esta função pressupõe que o arquivo de entrada esteja em formato JSON
        tradicional carregável por `json.load`, e não em JSON Lines.
    """

    caminho = Path("data") / f"{endpoint_pai}.json"

    with open(caminho) as f:
        dados = json.load(f)

    return [registro[campo_id] for registro in dados]
