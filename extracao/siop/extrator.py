"""Orquestrador da extração do SIOP — anos, partições e consolidação anual."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase

from .arquivos import SiopArquivos
from .cliente import SiopClienteSPARQL
from .estado import SiopEstadoRepositorio
from .paginador import SiopPaginador
from .queries import SiopQueryBuilder
from .transformador import SiopTransformador


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExtratorSIOP(ExtratorBase):
    """Orquestra a extração do SIOP com partições paralelas e retomada local.

    Estratégia:
    - ano → função orçamentária → página de IDs → lote de detalhes;
    - retomada por partição via arquivo de estado;
    - escrita incremental com promoção atômica ao final;
    - reaproveitamento de partições e arquivos anuais já válidos.

    Paralelismo:
    - Nível 1 (partições): funções orçamentárias extraídas em paralelo via
      ThreadPoolExecutor(max_workers_particoes).
    - Nível 2 (detalhes): lotes de detalhes dentro de cada partição via
      ThreadPoolExecutor delegado ao SiopPaginador.
    """

    _FLUSH_INTERVAL = 5

    def __init__(self) -> None:
        super().__init__("siop")

        config = obter_parametros_extrator("siop")

        self.funcoes_orcamentarias = tuple(config.get("funcoes_orcamentarias", ()))
        self.max_workers_particoes: int = config.get("max_workers_particoes", 6)

        caminho_salvo = Path("siop")
        estado_dir = Path("data/_estado/siop")

        self._arquivos = SiopArquivos(caminho_salvo, estado_dir)

        self._query_builder = SiopQueryBuilder(
            max_query_length=config.get("max_query_length"),
        )

        self._transformador = SiopTransformador()

        self._cliente = SiopClienteSPARQL(
            base_url=self.base_url,
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )

        self._estado = SiopEstadoRepositorio(
            arquivos=self._arquivos,
            page_size_inicial=config.get("page_size_inicial"),
        )

        self._paginador = SiopPaginador(
            cliente=self._cliente,
            query_builder=self._query_builder,
            transformador=self._transformador,
            page_size_inicial=config.get("page_size_inicial"),
            page_size_minima=config.get("page_size_minima"),
            detail_batch_size=config.get("detail_batch_size"),
            max_workers_detalhes=config.get("max_workers_detalhes", 2),
        )

    def _anos_locais(self) -> list[int]:
        """Infere anos já tocados a partir de saídas e checkpoints locais.

        Usa glob restrito a 2 níveis em vez de rglob("*") para evitar varrer
        toda a árvore de partições a cada inicialização.
        """

        anos: set[int] = set()
        padrao = re.compile(r"(?:orcamento_item_despesa_|ano=)(\d{4})")

        base = Path("data") / "siop"
        estado_dir = Path("data/_estado/siop")

        for diretorio in [base, estado_dir]:
            if not diretorio.exists():
                continue
            for caminho in (*diretorio.glob("*.json*"), *diretorio.glob("ano=*/")):
                match = padrao.search(str(caminho))
                if match:
                    anos.add(int(match.group(1)))

        return sorted(anos, reverse=True)

    def _anos_priorizados(self) -> list[int]:
        """Monta a fila de anos sem depender de uma discovery global cara."""

        ano_atual = datetime.now().year
        ano_fechado = ano_atual - 1
        fila = [ano_fechado, ano_atual]
        fila.extend(ano for ano in self._anos_locais() if ano not in {ano_fechado, ano_atual})
        fila.extend(range(ano_atual - 2, 2009, -1))

        ordenados: list[int] = []
        vistos: set[int] = set()

        for ano in fila:
            if ano < 2010 or ano in vistos:
                continue
            vistos.add(ano)
            ordenados.append(ano)

        return ordenados

    # ── extração de partição ─────────────────────────────────────────────────

    def _extrair_particao(
        self,
        ano: int,
        funcao_codigo: str,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ) -> dict:
        """Extrai uma partição `ano x função` com retomada local.

        Delega a escrita incremental a SiopArquivos.stream_jsonl() e a
        paginação a _gerador_com_rastreio().
        """

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
        elif caminho_empty.exists():
            retrying_from_empty = True

        estado = self._estado.carregar(ano, funcao_codigo)
        estado = self._estado.reconciliar_com_tmp(ano, funcao_codigo, estado)

        if estado["records"] == 0 and caminho_tmp.exists():
            caminho_tmp.unlink()

        estado["status"] = "running"
        estado["attempts"] = int(estado.get("attempts") or 0) + 1
        estado["message"] = None
        estado["updated_at"] = _agora_iso()
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

            total_final = estado["records"]  # atualizado pelo gerador

            if total_final == 0:
                if caminho_tmp.exists():
                    caminho_tmp.unlink()
                if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                    caminho_empty,
                    contexto=f"siop:ano={ano}:funcao={funcao_codigo}",
                ):
                    return self._extrair_particao(
                        ano, funcao_codigo, _allow_empty_retry=False, _from_empty_retry=True
                    )
                if not _from_empty_retry:
                    caminho_empty.touch()
                elif caminho_empty.exists():
                    caminho_empty.unlink()
                self._estado.marcar_final(
                    ano, funcao_codigo, estado, status="empty", message="particao sem registros"
                )
                return {"status": "empty", "records": 0, "pages": 0}

            if caminho_empty.exists():
                caminho_empty.unlink()
            self._estado.marcar_final(ano, funcao_codigo, estado, status="success")
            return {"status": "success", "records": total_final, "pages": estado["pages"]}

        except Exception as exc:
            self._estado.marcar_final(
                ano, funcao_codigo, estado, status="error", message=str(exc)[:1000]
            )
            raise

    def _gerador_com_rastreio(
        self,
        ano: int,
        funcao_codigo: str,
        estado: dict,
    ) -> Generator[dict, None, None]:
        """Envolve o paginador atualizando o checkpoint a cada página.

        Separa a responsabilidade de rastreio de paginação (estado, checkpoint,
        logs) da lógica de escrita (stream_jsonl). O cursor `last_item_uri` é
        lido do estado na entrada e atualizado após cada página.
        """

        tamanho: int = int(estado.get("page_size") or self._paginador._page_size_inicial)
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
                ano, funcao_codigo, last_item_uri, tamanho
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
            estado["updated_at"] = _agora_iso()
            self._estado.salvar(ano, funcao_codigo, estado)

            if len(item_uris) < tamanho:
                break

    # ── consolidação anual ───────────────────────────────────────────────────

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

    # ── extração de ano ──────────────────────────────────────────────────────

    def _extrair_ano(
        self,
        ano: int,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ) -> dict:
        """Extrai todas as partições de um ano e consolida o arquivo final.

        Paralelismo nível 1: partições submetidas em simultâneo ao
        ThreadPoolExecutor(max_workers_particoes). Cada thread possui sua
        própria sessão HTTP via SiopClienteSPARQL._local. Falhas individuais
        são registradas mas não abortam o ano.
        """

        arq = self._arquivos
        arq.saida_ano(ano).parent.mkdir(parents=True, exist_ok=True)
        retrying_from_empty = _from_empty_retry

        if arq.ano_pronto(ano):
            self.logger.info("[SIOP] Ano %s ja existe, pulando.", ano)
            return {"status": "skipped", "records": 0, "pages": 0}

        if arq.empty_ano(ano).exists() and not (
            _allow_empty_retry
            and self._consumir_retry_empty(
                arq.empty_ano(ano), contexto=f"siop:ano={ano}"
            )
        ):
            self.logger.info("[SIOP] Ano %s ja foi marcado como vazio, pulando.", ano)
            return {"status": "skipped_empty", "records": 0, "pages": 0}
        elif arq.empty_ano(ano).exists():
            retrying_from_empty = True

        try:
            query_probe = self._query_builder.probe_ano(ano)
            if not self._cliente.ano_tem_dados(query_probe, ano):
                if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                    arq.empty_ano(ano), contexto=f"siop:ano={ano}"
                ):
                    return self._extrair_ano(
                        ano, _allow_empty_retry=False, _from_empty_retry=True
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

        # ── paralelismo nível 1 ───────────────────────────────────────────────
        funcoes = list(self.funcoes_orcamentarias)
        falhas: list[tuple[str, BaseException]] = []

        with ThreadPoolExecutor(
            max_workers=min(self.max_workers_particoes, len(funcoes)),
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
        # ─────────────────────────────────────────────────────────────────────

        if falhas:
            self.logger.warning(
                "[SIOP] %s particao(oes) falharam no ano %s: %s — consolidando o restante.",
                len(falhas),
                ano,
                [f for f, _ in falhas],
            )

        return self._mesclar_particoes_ano(ano)

    # ── ponto de entrada ─────────────────────────────────────────────────────

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