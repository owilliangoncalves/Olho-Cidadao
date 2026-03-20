"""Gestão de caminhos e escrita incremental de arquivos JSONL do SIOP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from utils.jsonl import arquivo_jsonl_tem_chaves

# Intervalo padrão de flush — pode ser sobrescrito por chamada
_FLUSH_INTERVAL_PADRAO = 5

REQUIRED_OUTPUT_KEYS: frozenset[str] = frozenset(
    {
        "uri_item",
        "grafo_orcamentario_uri",
        "uri_funcao",
        "uri_subfuncao",
        "uri_programa",
        "uri_acao",
        "uri_unidade_orcamentaria",
        "codigo_unidade_orcamentaria",
        "uri_fonte",
        "codigo_fonte",
        "uri_gnd",
        "codigo_gnd",
        "uri_modalidade",
        "codigo_modalidade",
        "uri_elemento",
        "codigo_elemento",
        "orgao_origem",
    }
)


class SiopArquivos:
    """Centraliza caminhos de arquivo e a escrita incremental em JSONL.

    Responsabilidade única: saber *onde* os dados vivem no disco e como
    gravá-los de forma segura (tmp → replace atômico).

    Não conhece HTTP, SPARQL, estado de paginação nem lógica de negócio.
    """

    def __init__(self, caminho_salvo: Path, estado_dir: Path) -> None:
        self._base = Path("data") / caminho_salvo
        self._estado_dir = estado_dir

    @property
    def base_dir(self) -> Path:
        """Diretório base de saída do pacote."""

        return self._base

    @property
    def state_dir(self) -> Path:
        """Diretório onde os checkpoints das partições são persistidos."""

        return self._estado_dir

    @staticmethod
    def _marcador(caminho: Path, suffix: str) -> Path:
        """Deriva um arquivo marcador a partir do arquivo final."""

        return caminho.with_suffix(caminho.suffix + suffix)

    # ── caminhos anuais ──────────────────────────────────────────────────────

    def saida_ano(self, ano: int) -> Path:
        """Arquivo final consolidado do ano."""
        return self._base / f"orcamento_item_despesa_{ano}.jsonl"

    def tmp_ano(self, ano: int) -> Path:
        return self._marcador(self.saida_ano(ano), ".tmp")

    def empty_ano(self, ano: int) -> Path:
        return self._marcador(self.saida_ano(ano), ".empty")

    def ano_pronto(self, ano: int) -> bool:
        """True quando o arquivo anual existe e contém todas as chaves exigidas."""
        return arquivo_jsonl_tem_chaves(self.saida_ano(ano), REQUIRED_OUTPUT_KEYS)

    # ── caminhos de partição ─────────────────────────────────────────────────

    def saida_particao(self, ano: int, funcao_codigo: str) -> Path:
        return self._base / "_particoes" / f"ano={ano}" / f"funcao={funcao_codigo}.jsonl"

    def tmp_particao(self, ano: int, funcao_codigo: str) -> Path:
        return self._marcador(self.saida_particao(ano, funcao_codigo), ".tmp")

    def empty_particao(self, ano: int, funcao_codigo: str) -> Path:
        return self._marcador(self.saida_particao(ano, funcao_codigo), ".empty")

    def estado_particao(self, ano: int, funcao_codigo: str) -> Path:
        return (
            self._estado_dir
            / "particoes"
            / f"ano={ano}"
            / f"funcao={funcao_codigo}.state.json"
        )

    def particao_pronta(self, ano: int, funcao_codigo: str) -> bool:
        """True quando a partição existe e contém todas as chaves exigidas."""
        return arquivo_jsonl_tem_chaves(
            self.saida_particao(ano, funcao_codigo), REQUIRED_OUTPUT_KEYS
        )

    # ── escrita incremental ──────────────────────────────────────────────────

    def stream_jsonl(
        self,
        registros: Iterable[dict],
        destino: str | Path,
        modo: str = "w",
        flush_interval: int = _FLUSH_INTERVAL_PADRAO,
    ) -> int:
        """Consome um gerador de registros e salva em JSONL de forma incremental.

        Escreve em `.tmp` e só promove atomicamente ao destino final após
        esgotar o gerador sem erros. Em modo append ("a"), o .tmp recebe os
        novos registros sem apagar o conteúdo anterior.

        Args:
            registros:      Gerador que produz dicts um a um.
            destino:        Caminho do arquivo final.
            modo:           "w" (sobrescreve) ou "a" (acrescenta).
            flush_interval: Registros entre flushes explícitos.

        Returns:
            Número de registros escritos na chamada atual.
        """

        caminho = Path(destino)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho_tmp = caminho.with_suffix(caminho.suffix + ".tmp")

        total = 0
        with open(caminho_tmp, modo, encoding="utf-8") as f:
            for registro in registros:
                json.dump(registro, f, ensure_ascii=False)
                f.write("\n")
                total += 1
                if total % flush_interval == 0:
                    f.flush()
            f.flush()

        caminho_tmp.replace(caminho)

        return total
