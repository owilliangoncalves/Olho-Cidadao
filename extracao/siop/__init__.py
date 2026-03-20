"""Pacote SIOP com fachada pública e orquestração concentradas aqui."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import cache
from typing import Any
from typing import Generator

from extracao.siop.arquivos import SiopArquivos
from extracao.siop.cliente import SiopClienteSPARQL
from extracao.siop.config import SiopConfig
from extracao.siop.estado import SiopEstadoRepositorio
from extracao.siop.paginador import SiopPaginador
from extracao.siop.queries import SiopQueryBuilder
from extracao.siop.tarefas import agora_iso
from extracao.siop.tarefas import anos_locais
from extracao.siop.tarefas import anos_priorizados
from extracao.siop.transformador import SiopTransformador


@cache
def _construir_siop():
    """Cria e memoriza o orquestrador público do pacote."""

    from extracao.extrator_da_base import ExtratorBase

    class SIOP(ExtratorBase):
        """Orquestra a extração do SIOP com partições paralelas e retomada local."""

        _FLUSH_INTERVAL = 5

        def __init__(self) -> None:
            self.cfg = SiopConfig.carregar()
            super().__init__("siop")

            self.funcoes_orcamentarias = self.cfg.funcoes_orcamentarias
            self._arquivos = SiopArquivos(self.cfg.output_dir, self.cfg.state_dir)
            self._query_builder = SiopQueryBuilder(
                max_query_length=self.cfg.max_query_length,
            )
            self._transformador = SiopTransformador()
            self._cliente = SiopClienteSPARQL(
                base_url=self.base_url,
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )
            self._estado = SiopEstadoRepositorio(
                arquivos=self._arquivos,
                page_size_inicial=self.cfg.page_size_inicial,
            )
            self._paginador = SiopPaginador(
                cliente=self._cliente,
                query_builder=self._query_builder,
                transformador=self._transformador,
                page_size_inicial=self.cfg.page_size_inicial,
                page_size_minima=self.cfg.page_size_minima,
                detail_batch_size=self.cfg.detail_batch_size,
                max_workers_detalhes=self.cfg.max_workers_detalhes,
            )

        def _anos_locais(self) -> list[int]:
            """Infere os anos já tocados a partir do disco local."""

            return anos_locais(self._arquivos.base_dir, self._arquivos.state_dir)

        def _anos_priorizados(self) -> list[int]:
            """Monta a fila de anos priorizando exercícios mais úteis primeiro."""

            return anos_priorizados(self._anos_locais())

        def _extrair_particao(
            self,
            ano: int,
            funcao_codigo: str,
            _allow_empty_retry: bool = True,
            _from_empty_retry: bool = False,
        ) -> dict:
            """Extrai uma partição `ano x função` com retomada local."""

            arq = self._arquivos
            caminho_saida = arq.saida_particao(ano, funcao_codigo)
            caminho_tmp = arq.tmp_particao(ano, funcao_codigo)
            caminho_empty = arq.empty_particao(ano, funcao_codigo)
            caminho_saida.parent.mkdir(parents=True, exist_ok=True)
            retrying_from_empty = _from_empty_retry

            if arq.particao_pronta(ano, funcao_codigo):
                if caminho_empty.exists():
                    caminho_empty.unlink()
                self.logger.info(
                    "[SIOP] Particao ja existe, pulando | ano=%s | funcao=%s",
                    ano,
                    funcao_codigo,
                )
                return {"status": "skipped", "records": 0, "pages": 0}

            if caminho_empty.exists() and not (
                _allow_empty_retry
                and self._consumir_retry_empty(
                    caminho_empty,
                    contexto=f"siop:ano={ano}:funcao={funcao_codigo}",
                )
            ):
                self.logger.info(
                    "[SIOP] Particao vazia ja confirmada, pulando | ano=%s | funcao=%s",
                    ano,
                    funcao_codigo,
                )
                return {"status": "skipped_empty", "records": 0, "pages": 0}
            if caminho_empty.exists():
                retrying_from_empty = True

            estado = self._estado.carregar(ano, funcao_codigo)
            estado = self._estado.reconciliar_com_tmp(ano, funcao_codigo, estado)

            if estado["records"] == 0 and caminho_tmp.exists():
                caminho_tmp.unlink()

            estado["status"] = "running"
            estado["attempts"] = int(estado.get("attempts") or 0) + 1
            estado["message"] = None
            estado["updated_at"] = agora_iso()
            self._estado.salvar(ano, funcao_codigo, estado)

            modo = "a" if estado["records"] > 0 and caminho_tmp.exists() else "w"
            gerador = self._gerador_com_rastreio(ano, funcao_codigo, estado)

            try:
                arq.stream_jsonl(
                    registros=gerador,
                    destino=caminho_saida,
                    modo=modo,
                    flush_interval=self._FLUSH_INTERVAL,
                )

                total_final = estado["records"]

                if total_final == 0:
                    if caminho_tmp.exists():
                        caminho_tmp.unlink()
                    if (
                        not retrying_from_empty
                        and _allow_empty_retry
                        and self._consumir_retry_empty(
                            caminho_empty,
                            contexto=f"siop:ano={ano}:funcao={funcao_codigo}",
                        )
                    ):
                        return self._extrair_particao(
                            ano,
                            funcao_codigo,
                            _allow_empty_retry=False,
                            _from_empty_retry=True,
                        )
                    if not _from_empty_retry:
                        caminho_empty.touch()
                    elif caminho_empty.exists():
                        caminho_empty.unlink()
                    self._estado.marcar_final(
                        ano,
                        funcao_codigo,
                        estado,
                        status="empty",
                        message="particao sem registros",
                    )
                    return {"status": "empty", "records": 0, "pages": 0}

                if caminho_empty.exists():
                    caminho_empty.unlink()
                self._estado.marcar_final(ano, funcao_codigo, estado, status="success")
                return {"status": "success", "records": total_final, "pages": estado["pages"]}

            except Exception as exc:
                self._estado.marcar_final(
                    ano,
                    funcao_codigo,
                    estado,
                    status="error",
                    message=str(exc)[:1000],
                )
                raise

        def _gerador_com_rastreio(
            self,
            ano: int,
            funcao_codigo: str,
            estado: dict,
        ) -> Generator[dict, None, None]:
            """Atualiza o checkpoint a cada página detalhada da partição."""

            tamanho = int(estado.get("page_size") or self._paginador.page_size_inicial)
            last_item_uri: str | None = estado.get("last_item_uri")

            while True:
                self.logger.info(
                    "[SIOP] Ano %s | funcao=%s | offset=%s | paginas=%s | registros=%s | page_size=%s",
                    ano,
                    funcao_codigo,
                    estado["offset"],
                    estado["pages"],
                    estado["records"],
                    tamanho,
                )

                item_uris, tamanho = self._paginador.buscar_ids_pagina(
                    ano,
                    funcao_codigo,
                    last_item_uri,
                    tamanho,
                )
                estado["page_size"] = tamanho

                if not item_uris:
                    break

                registros = self._paginador.coletar_registros_detalhados(ano, item_uris)

                yield from registros

                estado["records"] += len(registros)
                estado["pages"] += 1
                estado["offset"] += len(item_uris)
                last_item_uri = item_uris[-1]
                estado["last_item_uri"] = last_item_uri
                estado["updated_at"] = agora_iso()
                self._estado.salvar(ano, funcao_codigo, estado)

                if len(item_uris) < tamanho:
                    break

        def _mesclar_particoes_ano(self, ano: int) -> dict:
            """Monta o arquivo anual final a partir das partições concluídas."""

            arq = self._arquivos
            caminho_final = arq.saida_ano(ano)
            caminho_tmp = arq.tmp_ano(ano)
            caminho_empty = arq.empty_ano(ano)

            if caminho_tmp.exists():
                caminho_tmp.unlink()

            def _gerador_particoes() -> Generator[dict, None, None]:
                for funcao_codigo in self.funcoes_orcamentarias:
                    caminho_particao = arq.saida_particao(ano, funcao_codigo)
                    if not caminho_particao.exists():
                        continue
                    with open(caminho_particao, encoding="utf-8") as origem:
                        for linha in origem:
                            linha = linha.strip()
                            if not linha:
                                continue
                            yield json.loads(linha)

            total = arq.stream_jsonl(registros=_gerador_particoes(), destino=caminho_final)

            if total == 0:
                if caminho_final.exists():
                    caminho_final.unlink()
                caminho_empty.touch()
                self.logger.warning("[SIOP] Ano %s consolidado como vazio.", ano)
                return {"status": "empty", "records": 0, "pages": 0}

            if caminho_empty.exists():
                caminho_empty.unlink()
            self.logger.info(
                "[SIOP] Ano %s consolidado | registros=%s | arquivo=%s",
                ano,
                total,
                caminho_final,
            )
            return {"status": "success", "records": total, "pages": 0}

        def _extrair_ano(
            self,
            ano: int,
            _allow_empty_retry: bool = True,
            _from_empty_retry: bool = False,
        ) -> dict:
            """Extrai todas as partições de um ano e consolida o arquivo final."""

            arq = self._arquivos
            arq.saida_ano(ano).parent.mkdir(parents=True, exist_ok=True)
            retrying_from_empty = _from_empty_retry

            if arq.ano_pronto(ano):
                self.logger.info("[SIOP] Ano %s ja existe, pulando.", ano)
                return {"status": "skipped", "records": 0, "pages": 0}

            if arq.empty_ano(ano).exists() and not (
                _allow_empty_retry
                and self._consumir_retry_empty(
                    arq.empty_ano(ano),
                    contexto=f"siop:ano={ano}",
                )
            ):
                self.logger.info("[SIOP] Ano %s ja foi marcado como vazio, pulando.", ano)
                return {"status": "skipped_empty", "records": 0, "pages": 0}
            if arq.empty_ano(ano).exists():
                retrying_from_empty = True

            try:
                query_probe = self._query_builder.probe_ano(ano)
                if not self._cliente.ano_tem_dados(query_probe, ano):
                    if (
                        not retrying_from_empty
                        and _allow_empty_retry
                        and self._consumir_retry_empty(
                            arq.empty_ano(ano),
                            contexto=f"siop:ano={ano}",
                        )
                    ):
                        return self._extrair_ano(
                            ano,
                            _allow_empty_retry=False,
                            _from_empty_retry=True,
                        )
                    if not _from_empty_retry:
                        arq.empty_ano(ano).touch()
                    elif arq.empty_ano(ano).exists():
                        arq.empty_ano(ano).unlink()
                    self.logger.info("[SIOP] Ano %s sem dados no probe leve, pulando.", ano)
                    return {"status": "empty", "records": 0, "pages": 0}
            except Exception as exc:
                self.logger.warning(
                    "[SIOP] Probe leve falhou para o ano %s (%s). Seguindo para as particoes.",
                    ano,
                    exc,
                )

            funcoes = list(self.funcoes_orcamentarias)
            falhas: list[tuple[str, BaseException]] = []

            with ThreadPoolExecutor(
                max_workers=min(self.cfg.max_workers_particoes, len(funcoes)),
                thread_name_prefix=f"siop-{ano}",
            ) as pool:
                futuros = {
                    pool.submit(self._extrair_particao, ano, funcao): funcao
                    for funcao in funcoes
                }

                for futuro in as_completed(futuros):
                    funcao = futuros[futuro]
                    try:
                        futuro.result()
                    except Exception as exc:
                        falhas.append((funcao, exc))
                        self.logger.error(
                            "[SIOP] Falha na particao | ano=%s | funcao=%s | %s",
                            ano,
                            funcao,
                            exc,
                        )

            if falhas:
                self.logger.warning(
                    "[SIOP] %s particao(oes) falharam no ano %s: %s — consolidando o restante.",
                    len(falhas),
                    ano,
                    [funcao for funcao, _ in falhas],
                )

            return self._mesclar_particoes_ano(ano)

        def executar(self) -> None:
            """Executa a extração do SIOP priorizando os anos mais úteis primeiro."""

            anos = self._anos_priorizados()
            self.logger.info("[SIOP] Iniciando extracao do endpoint SPARQL.")
            self.logger.info("[SIOP] Anos priorizados para extracao: %s", anos)

            if not anos:
                self.logger.warning("[SIOP] Nenhum ano disponivel foi encontrado.")
                return

            stats = {"completed": 0, "skipped": 0, "empty": 0, "failed": 0}

            for ano in anos:
                try:
                    resumo = self._extrair_ano(ano)
                except Exception:
                    stats["failed"] += 1
                    self.logger.exception("[SIOP] Falha critica no ano %s", ano)
                    continue

                status = resumo["status"]
                if status == "success":
                    stats["completed"] += 1
                elif status in {"skipped", "skipped_empty"}:
                    stats["skipped"] += 1
                elif status == "empty":
                    stats["empty"] += 1

            self.logger.info(
                "[SIOP] Extracao concluida | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
                stats["completed"],
                stats["skipped"],
                stats["empty"],
                stats["failed"],
            )

    SIOP.__module__ = __name__
    return SIOP


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "SIOP":
        siop = _construir_siop()
        globals()[name] = siop
        return siop
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantém introspecção consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "SIOP",
    "SiopArquivos",
    "SiopClienteSPARQL",
    "SiopConfig",
    "SiopEstadoRepositorio",
    "SiopPaginador",
    "SiopQueryBuilder",
    "SiopTransformador",
    "anos_locais",
    "anos_priorizados",
]
