"""Artefatos e estado persistido do extrator de CEAPS do Senado."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infra.estado.arquivos import derivar_artefatos_tarefa
from utils.jsonl import arquivo_jsonl_tem_chaves

SENADO_STATE_ROOT = Path("data/_estado/senado")
SENADO_REQUIRED_OUTPUT_KEYS = {
    "documento_fornecedor_normalizado",
    "tipo_documento_fornecedor",
    "cnpj_base_fornecedor",
    "orgao_origem",
    "endpoint_origem",
    "ano_arquivo",
}


@dataclass(frozen=True)
class SenadoArquivosAno:
    """Encapsula os caminhos persistidos de um exercicio anual do Senado."""

    ano: int
    saida: Path
    temporario: Path
    empty: Path
    estado: Path

    def pronto(self) -> bool:
        """Indica se ja existe um arquivo final reaproveitavel para o ano."""

        return arquivo_jsonl_tem_chaves(self.saida, SENADO_REQUIRED_OUTPUT_KEYS)


def artefatos_ano_senado(ano: int) -> SenadoArquivosAno:
    """Deriva os artefatos persistidos de um exercicio anual."""

    saida, estado, temporario, empty = derivar_artefatos_tarefa(
        Path("senadores") / f"ceaps_{ano}.json",
        state_root=SENADO_STATE_ROOT,
    )
    return SenadoArquivosAno(
        ano=ano,
        saida=saida,
        temporario=temporario,
        empty=empty,
        estado=estado,
    )


def estado_inicial_senado() -> dict:
    """Retorna o estado inicial da tarefa anual."""

    return {
        "status": "pending",
        "attempts": 0,
        "records": 0,
    }
