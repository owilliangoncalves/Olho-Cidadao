"""Persistência e reconciliação do estado de progresso das partições do SIOP."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from utils.jsonl import contar_registros_jsonl

from extracao.siop.arquivos import SiopArquivos
from extracao.siop.tarefas import agora_iso

logger = logging.getLogger(__name__)


class SiopEstadoRepositorio:
    """Lê, grava e reconcilia o checkpoint de cada partição `ano x função`.

    Responsabilidade única: saber *como* persiste e recupera o estado de
    progresso — sem lógica de HTTP, SPARQL ou transformação de dados.
    """

    _SCHEMA_VERSION = 4

    def __init__(self, arquivos: SiopArquivos, page_size_inicial: int) -> None:
        self._arquivos = arquivos
        self._page_size_inicial = page_size_inicial

    # ── estrutura de estado ──────────────────────────────────────────────────

    def inicial(self) -> dict:
        """Retorna a estrutura padrão de estado de uma partição nova."""

        return {
            "schema_version": self._SCHEMA_VERSION,
            "status": "pending",
            "attempts": 0,
            "offset": 0,
            "pages": 0,
            "records": 0,
            "page_size": self._page_size_inicial,
            "last_item_uri": None,
            "message": None,
            "updated_at": None,
        }

    # ── leitura e escrita ────────────────────────────────────────────────────

    def carregar(self, ano: int, funcao_codigo: str) -> dict:
        """Lê o estado salvo da partição."""

        estado = self.inicial()
        caminho = self._arquivos.estado_particao(ano, funcao_codigo)

        if not caminho.exists():
            return estado

        try:
            with open(caminho, encoding="utf-8") as f:
                carregado = json.load(f)
        except json.JSONDecodeError:
            return estado

        if not isinstance(carregado, dict):
            return estado

        for chave in estado:
            if chave in carregado:
                estado[chave] = carregado[chave]

        return estado

    def salvar(self, ano: int, funcao_codigo: str, estado: dict) -> None:
        """Persiste o estado da partição em disco."""

        caminho = self._arquivos.estado_particao(ano, funcao_codigo)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False)

    # ── reconciliação ────────────────────────────────────────────────────────

    def reconciliar_com_tmp(self, ano: int, funcao_codigo: str, estado: dict) -> dict:
        """Alinha o checkpoint ao conteúdo real do arquivo temporário."""

        caminho_tmp = self._arquivos.tmp_particao(ano, funcao_codigo)

        if not caminho_tmp.exists():
            if estado["status"] == "running":
                estado["status"] = "pending"
            estado.update(offset=0, pages=0, records=0, last_item_uri=None)
            return estado

        total_tmp = contar_registros_jsonl(caminho_tmp)
        if total_tmp == 0:
            estado.update(offset=0, pages=0, records=0, last_item_uri=None)
            return estado

        ultima_uri_tmp = self._ultima_uri_item_tmp(caminho_tmp)

        if estado["records"] != total_tmp or estado["offset"] < total_tmp:
            logger.warning(
                "[SIOP] Reconciliando particao | ano=%s | funcao=%s | "
                "estado=(offset=%s,paginas=%s,registros=%s) | tmp_registros=%s",
                ano,
                funcao_codigo,
                estado["offset"],
                estado["pages"],
                estado["records"],
                total_tmp,
            )
            estado["records"] = total_tmp
            estado["offset"] = max(int(estado.get("offset") or 0), total_tmp)

        if ultima_uri_tmp and estado.get("last_item_uri") != ultima_uri_tmp:
            estado["last_item_uri"] = ultima_uri_tmp

        return estado

    def marcar_final(
        self,
        ano: int,
        funcao_codigo: str,
        estado: dict,
        status: str,
        message: str | None = None,
    ) -> None:
        """Persiste o estado final de uma partição (sucesso, erro, vazio)."""

        estado["status"] = status
        estado["message"] = message
        estado["updated_at"] = agora_iso()
        self.salvar(ano, funcao_codigo, estado)

    # ── helper interno ───────────────────────────────────────────────────────

    def _ultima_uri_item_tmp(self, caminho_tmp: Path) -> str | None:
        """Busca a última uri_item lendo de trás para frente em blocos de 8 KB.

        Evita ler o arquivo inteiro: em retomadas com dezenas de MB o ganho de
        startup por thread é significativo. Na maioria dos casos a última linha
        válida está nos primeiros 8 KB lidos — o while executa uma iteração.
        """

        try:
            with open(caminho_tmp, "rb") as f:
                f.seek(0, 2)
                tamanho = f.tell()
                if tamanho == 0:
                    return None

                bloco = 8192
                buffer = b""
                pos = tamanho

                while pos > 0:
                    pos = max(0, pos - bloco)
                    f.seek(pos)
                    chunk = f.read(min(bloco, tamanho - pos))
                    buffer = chunk + buffer

                    for linha in reversed(buffer.split(b"\n")):
                        linha = linha.strip()
                        if not linha:
                            continue
                        try:
                            uri = json.loads(linha).get("uri_item")
                            if uri:
                                return uri
                        except json.JSONDecodeError:
                            continue

                    if b'"uri_item"' in buffer:
                        break

        except OSError:
            pass

        return None
