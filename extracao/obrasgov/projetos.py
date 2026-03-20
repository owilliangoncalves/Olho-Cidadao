"""Helpers de leitura local de projetos e identificadores do ObrasGov."""

from __future__ import annotations

import json
import re
from pathlib import Path


def slug_id(valor: str) -> str:
    """Normaliza um identificador para uso em nome de arquivo."""

    return re.sub(r"[^0-9A-Za-z._-]+", "-", valor).strip("-") or "desconhecido"


def iterar_arquivos_projetos(base_dir: Path | None = None) -> list[Path]:
    """Lista arquivos de projetos, incluindo `.tmp` sem final correspondente."""

    caminho = base_dir or Path("data/obrasgov/projeto-investimento")
    if not caminho.exists():
        return []

    arquivos_finais = sorted(caminho.glob("**/*.json"))
    arquivos_temporarios = sorted(
        arquivo for arquivo in caminho.glob("**/*.json.tmp") if not arquivo.with_suffix("").exists()
    )
    return [*arquivos_finais, *arquivos_temporarios]


def iterar_ids_projetos(base_dir: Path | None = None):
    """Lê `idUnico` dos projetos finalizados ou já persistidos em `.tmp`."""

    arquivos = iterar_arquivos_projetos(base_dir=base_dir)
    if not arquivos:
        return

    vistos: set[str] = set()
    for arquivo in arquivos:
        with open(arquivo, encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                try:
                    registro = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                payload = registro.get("payload", {})
                id_unico = payload.get("idUnico")
                if not id_unico or id_unico in vistos:
                    continue

                vistos.add(id_unico)
                yield id_unico
