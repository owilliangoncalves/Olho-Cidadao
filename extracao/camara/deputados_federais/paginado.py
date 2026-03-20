"""Execução paginada com retomada para JSON Lines da Câmara."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.paginacao import proxima_pagina

from .artefatos import ArtefatosExtracao


def estado_inicial(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """Retorna o estado inicial padrão da paginação."""

    return {
        "page": 1,
        "pages": 0,
        "records": 0,
        "next_url": url,
        "params": params,
    }


def executar_jsonl_paginado(
    *,
    extrator,
    artefatos: ArtefatosExtracao,
    required_output_keys: set[str] | frozenset[str],
    initial_url: str,
    initial_params: dict[str, Any],
    fetch_page: Callable[[str, dict[str, Any] | None], dict[str, Any]],
    extract_items: Callable[[dict[str, Any]], Any],
    transform_item: Callable[[dict[str, Any]], dict[str, Any]],
    empty_context: str,
    log_page: Callable[[int, list[dict[str, Any]]], None] | None = None,
    next_url_from_response: Callable[[dict[str, Any]], str | None] = proxima_pagina,
    allow_empty_retry: bool = True,
    from_empty_retry: bool = False,
) -> dict[str, int | str]:
    """Executa a extração incremental de um recurso paginado em JSONL."""

    retrying_from_empty = from_empty_retry

    if arquivo_jsonl_tem_chaves(artefatos.saida, required_output_keys):
        return {"status": "skipped", "records": 0, "pages": 0}

    if artefatos.empty.exists():
        if allow_empty_retry and extrator._consumir_retry_empty(
            artefatos.empty,
            contexto=empty_context,
        ):
            retrying_from_empty = True
        else:
            return {"status": "skipped_empty", "records": 0, "pages": 0}

    estado = carregar_estado_json(
        artefatos.estado,
        estado_inicial(initial_url, dict(initial_params)),
    )

    if estado["page"] > 1 and not artefatos.tmp.exists():
        estado = estado_inicial(initial_url, dict(initial_params))

    if estado["page"] == 1 and artefatos.tmp.exists():
        artefatos.tmp.unlink()

    if (
        estado.get("next_url") is None
        and int(estado.get("records", 0)) > 0
        and artefatos.tmp.exists()
    ):
        artefatos.tmp.replace(artefatos.saida)
        limpar_artefatos(artefatos.estado)
        return {
            "status": "success",
            "records": int(estado.get("records", 0)),
            "pages": int(estado.get("pages", 0)),
        }

    artefatos.tmp.parent.mkdir(parents=True, exist_ok=True)
    modo = "a" if int(estado["records"]) > 0 and artefatos.tmp.exists() else "w"
    pagina = int(estado["page"])
    paginas_escritas = int(estado["pages"])
    total_registros = int(estado["records"])
    url = estado["next_url"]
    params = estado.get("params")

    with open(artefatos.tmp, modo, encoding="utf-8") as destino:
        while url:
            resposta = fetch_page(url, params)
            itens = list(extract_items(resposta) or [])
            if not itens:
                break

            if log_page is not None:
                log_page(pagina, itens)

            for item in itens:
                json.dump(transform_item(item), destino, ensure_ascii=False)
                destino.write("\n")

            destino.flush()
            total_registros += len(itens)
            paginas_escritas += 1
            pagina += 1
            url = next_url_from_response(resposta)
            params = None

            salvar_estado_json(
                artefatos.estado,
                {
                    "page": pagina,
                    "pages": paginas_escritas,
                    "records": total_registros,
                    "next_url": url,
                    "params": params,
                },
            )

    if total_registros == 0:
        limpar_artefatos(artefatos.estado, artefatos.tmp)
        if (
            not retrying_from_empty
            and allow_empty_retry
            and extrator._consumir_retry_empty(artefatos.empty, contexto=empty_context)
        ):
            return executar_jsonl_paginado(
                extrator=extrator,
                artefatos=artefatos,
                required_output_keys=required_output_keys,
                initial_url=initial_url,
                initial_params=initial_params,
                fetch_page=fetch_page,
                extract_items=extract_items,
                transform_item=transform_item,
                empty_context=empty_context,
                log_page=log_page,
                next_url_from_response=next_url_from_response,
                allow_empty_retry=False,
                from_empty_retry=True,
            )

        if not from_empty_retry:
            artefatos.empty.touch()
        elif artefatos.empty.exists():
            artefatos.empty.unlink()

        return {"status": "empty", "records": 0, "pages": 0}

    if artefatos.empty.exists():
        artefatos.empty.unlink()

    artefatos.tmp.replace(artefatos.saida)
    limpar_artefatos(artefatos.estado)
    return {
        "status": "success",
        "records": total_registros,
        "pages": paginas_escritas,
    }
