"""Helpers compartilhados para checkpoints e retomada baseados em arquivos."""

from __future__ import annotations

import json
import re
from pathlib import Path


def slug_segmento(valor) -> str:
    """Normaliza um valor para uso seguro em nomes de diretório e arquivo."""

    texto = re.sub(r"[^0-9A-Za-z._=-]+", "-", str(valor)).strip("-")
    return texto or "vazio"


def carregar_estado_json(caminho: Path, estado_inicial: dict) -> dict:
    """Lê um arquivo de estado JSON, retornando um fallback em caso de falha."""

    if not caminho.exists():
        return dict(estado_inicial)

    try:
        with open(caminho, encoding="utf-8") as f:
            carregado = json.load(f)
    except json.JSONDecodeError:
        return dict(estado_inicial)

    if not isinstance(carregado, dict):
        return dict(estado_inicial)

    estado = dict(estado_inicial)
    estado.update(carregado)
    return estado


def salvar_estado_json(caminho: Path, estado: dict):
    """Persiste um dicionário JSON em disco, garantindo o diretório pai."""

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False)


def derivar_artefatos_tarefa(
    relative_output_path: Path,
    *,
    state_root: Path,
) -> tuple[Path, Path, Path, Path]:
    """Deriva caminhos final, temporário, vazio e de estado de uma tarefa."""

    output_path = Path("data") / relative_output_path
    state_path = state_root / relative_output_path.with_suffix(".state.json")
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    empty_path = output_path.with_suffix(output_path.suffix + ".empty")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path, state_path, tmp_path, empty_path


def limpar_artefatos(*caminhos: Path):
    """Remove um conjunto de artefatos temporários, ignorando ausências."""

    for caminho in caminhos:
        if caminho.exists():
            caminho.unlink()
