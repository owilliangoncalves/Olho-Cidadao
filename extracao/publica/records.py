"""Helpers de normalizacao e serializacao da base de APIs publicas."""

from __future__ import annotations

import json

DEFAULT_ITEM_KEYS = ("data", "items", "content", "resultado", "results")


def coerce_items(resposta, item_keys=DEFAULT_ITEM_KEYS):
    """Normaliza diferentes formatos de resposta para uma lista de itens."""

    if isinstance(resposta, list):
        return resposta

    if isinstance(resposta, dict):
        for chave in item_keys:
            valor = resposta.get(chave)
            if isinstance(valor, list):
                return valor

    return []


def build_record(item, *, context: dict, endpoint: str, orgao: str, nome_endpoint: str):
    """Empacota o payload com metadados minimos de rastreabilidade."""

    return {
        "_meta": {
            **context,
            "endpoint": endpoint,
            "orgao_origem": orgao.lower(),
            "nome_endpoint": nome_endpoint,
        },
        "payload": item,
    }


def write_jsonl_records(handle, items, *, build_record_fn) -> int:
    """Serializa itens em JSONL usando o envelope de registro informado."""

    total = 0
    for item in items:
        json.dump(build_record_fn(item), handle, ensure_ascii=False)
        handle.write("\n")
        total += 1
    return total
