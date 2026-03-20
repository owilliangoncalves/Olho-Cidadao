"""Paginação e coleta paralela de detalhes de itens de despesa do SIOP."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from extracao.siop.cliente import SiopClienteSPARQL
from extracao.siop.queries import SiopQueryBuilder
from extracao.siop.transformador import SiopTransformador

logger = logging.getLogger(__name__)


class SiopPaginador:
    """Busca páginas de IDs e coleta detalhes de itens em paralelo.

    Responsabilidade única: saber *como paginar* o endpoint e *como paralelizar*
    a coleta de detalhes — sem conhecer caminhos de arquivo, estado de
    checkpoint ou lógica de consolidação anual.

    Paralelismo nível 2: lotes de detalhes dentro de cada partição são
    submetidos em simultâneo ao ThreadPoolExecutor(max_workers_detalhes). O
    dict `detalhes_por_uri` é seguro para escrita concorrente sob o GIL do
    CPython, e a indexação por URI garante deduplicação sem lock explícito.
    A ordem original dos URIs é reconstituída ao final — crítico para o cursor
    de paginação.
    """

    def __init__(
        self,
        cliente: SiopClienteSPARQL,
        query_builder: SiopQueryBuilder,
        transformador: SiopTransformador,
        page_size_inicial: int,
        page_size_minima: int,
        detail_batch_size: int,
        max_workers_detalhes: int,
    ) -> None:
        self._cliente = cliente
        self._qb = query_builder
        self._transformador = transformador
        self._page_size_inicial = page_size_inicial
        self._page_size_minima = page_size_minima
        self._detail_batch_size = detail_batch_size
        self._max_workers_detalhes = max_workers_detalhes

    @property
    def page_size_inicial(self) -> int:
        """Expõe o tamanho inicial negociado para paginação."""

        return self._page_size_inicial

    # ── busca de IDs ─────────────────────────────────────────────────────────

    def buscar_ids_pagina(
        self,
        ano: int,
        funcao_codigo: str,
        last_item_uri: str | None,
        page_size: int,
    ) -> tuple[list[str], int]:
        """Busca os URIs da próxima página com redução adaptativa de carga.

        Reduz o page_size pela metade a cada falha até atingir o mínimo; erros
        400 (consulta rejeitada) abortam imediatamente sem tentar reduzir.
        """

        tamanho = max(self._page_size_minima, page_size)
        ultima_excecao: Exception | None = None

        while tamanho >= self._page_size_minima:
            try:
                query = self._qb.ids_pagina(ano, funcao_codigo, tamanho, last_item_uri)
                resposta = self._cliente.fazer_requisicao(query, ano=ano, timeout=(10, 30))
                bindings = resposta.get("results", {}).get("bindings", [])
                item_uris = [
                    item["item"]["value"]
                    for item in bindings
                    if item.get("item", {}).get("value")
                ]
                return item_uris, tamanho

            except Exception as exc:
                ultima_excecao = exc
                response = getattr(exc, "response", None)
                if getattr(response, "status_code", None) == 400:
                    logger.error(
                        "[SIOP] Consulta de IDs rejeitada (400) | ano=%s | funcao=%s | page_size=%s",
                        ano,
                        funcao_codigo,
                        tamanho,
                    )
                    break

                if tamanho == self._page_size_minima:
                    break

                proximo = max(self._page_size_minima, tamanho // 2)
                if proximo == tamanho:
                    break

                logger.warning(
                    "[SIOP] Reduzindo page_size | ano=%s | funcao=%s | de=%s para=%s",
                    ano,
                    funcao_codigo,
                    tamanho,
                    proximo,
                )
                tamanho = proximo

        raise ultima_excecao

    # ── busca de detalhes ────────────────────────────────────────────────────

    def buscar_detalhes_lote(self, ano: int, item_uris: list[str]) -> list[dict]:
        """Busca os detalhes de um lote, dividindo-o recursivamente quando necessário."""

        if not item_uris:
            return []

        query = self._qb.detalhes_itens(ano, item_uris)

        if self._qb.excede_limite_url(query):
            return self._dividir_e_buscar(ano, item_uris, motivo="limite de URL")

        try:
            resposta = self._cliente.fazer_requisicao(query, ano=ano, timeout=(15, 45))
            return resposta.get("results", {}).get("bindings", [])
        except Exception:
            if len(item_uris) <= 1:
                raise
            return self._dividir_e_buscar(ano, item_uris, motivo="erro na requisição")

    def _dividir_e_buscar(
        self, ano: int, item_uris: list[str], motivo: str
    ) -> list[dict]:
        """Divide o lote ao meio e busca cada metade recursivamente."""

        if len(item_uris) <= 1:
            raise ValueError(
                f"[SIOP] Consulta excede limite mesmo com um único item: {item_uris[0]}"
            )

        meio = len(item_uris) // 2
        esquerda, direita = item_uris[:meio], item_uris[meio:]
        logger.warning(
            "[SIOP] Dividindo lote (%s) | ano=%s | itens=%s -> %s + %s",
            motivo,
            ano,
            len(item_uris),
            len(esquerda),
            len(direita),
        )
        return self.buscar_detalhes_lote(ano, esquerda) + self.buscar_detalhes_lote(
            ano, direita
        )

    # ── coleta paralela ──────────────────────────────────────────────────────

    def coletar_registros_detalhados(self, ano: int, item_uris: list[str]) -> list[dict]:
        """Converte URIs de item em registros completos via lotes paralelos.

        A ordem original dos URIs é reconstituída ao final para preservar
        a consistência do cursor de paginação.
        """

        if not item_uris:
            return []

        lotes = [
            item_uris[i : i + self._detail_batch_size]
            for i in range(0, len(item_uris), self._detail_batch_size)
        ]

        detalhes_por_uri: dict[str, dict] = {}

        with ThreadPoolExecutor(
            max_workers=min(self._max_workers_detalhes, len(lotes)),
            thread_name_prefix=f"siop-det-{ano}",
        ) as pool:
            futuros = {
                pool.submit(self.buscar_detalhes_lote, ano, lote): lote
                for lote in lotes
            }

            for futuro in as_completed(futuros):
                try:
                    bindings = futuro.result()
                except Exception as exc:
                    lote = futuros[futuro]
                    logger.error(
                        "[SIOP] Falha em lote de detalhes | ano=%s | lote_size=%s | %s",
                        ano,
                        len(lote),
                        exc,
                    )
                    continue

                for item in bindings:
                    uri_item = self._transformador.binding_value(item, "item")
                    if uri_item and uri_item not in detalhes_por_uri:
                        detalhes_por_uri[uri_item] = item

        registros = []
        faltantes = 0

        for uri_item in item_uris:
            binding = detalhes_por_uri.get(uri_item)
            if binding is None:
                faltantes += 1
                binding = {"item": {"value": uri_item}}
            registros.append(self._transformador.transformar(ano, binding))

        if faltantes:
            logger.warning(
                "[SIOP] Itens sem enriquecimento completo | ano=%s | faltantes=%s",
                ano,
                faltantes,
            )

        return registros
