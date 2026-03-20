"""Artefatos e validacao de saida da base de APIs publicas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from infra.estado.arquivos import derivar_artefatos_tarefa
from utils.jsonl import arquivo_jsonl_meta_tem_chaves

PUBLICA_STATE_ROOT = Path("data/_estado/publica")


@dataclass(frozen=True)
class TaskArtifacts:
    output_path: Path
    state_path: Path
    tmp_path: Path
    empty_path: Path


def derivar_artefatos_publicos(relative_output_path: Path) -> TaskArtifacts:
    """Deriva os caminhos persistidos usados por uma tarefa da base publica."""

    output_path, state_path, tmp_path, empty_path = derivar_artefatos_tarefa(
        relative_output_path,
        state_root=PUBLICA_STATE_ROOT,
    )
    return TaskArtifacts(
        output_path=output_path,
        state_path=state_path,
        tmp_path=tmp_path,
        empty_path=empty_path,
    )


def output_pronto(
    output_path: Path,
    *,
    required_meta_keys: set[str],
    extra_meta_keys: set[str] | None = None,
) -> bool:
    """Indica se a saida existente ja contem o esquema minimo esperado."""

    required = set(required_meta_keys)
    if extra_meta_keys:
        required.update(extra_meta_keys)
    return arquivo_jsonl_meta_tem_chaves(output_path, required)
