"""Convenções de artefatos para a extração de deputados federais."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtefatosExtracao:
    """Agrupa os caminhos de saída, retomada e vazio de uma tarefa."""

    saida: Path
    tmp: Path
    empty: Path
    estado: Path


def _artefatos(saida: Path, estado: Path) -> ArtefatosExtracao:
    """Deriva todos os artefatos a partir do arquivo final."""

    return ArtefatosExtracao(
        saida=saida,
        tmp=saida.with_suffix(".json.tmp"),
        empty=saida.with_suffix(".json.empty"),
        estado=estado,
    )


def artefatos_legislaturas(saida: Path) -> ArtefatosExtracao:
    """Retorna os artefatos da lista mestre de legislaturas."""

    return _artefatos(
        saida=saida,
        estado=Path("data/_estado/camara/legislaturas.state.json"),
    )


def artefatos_deputados_legislatura(
    pasta_saida: Path,
    prefixo_arquivo: str,
    id_legislatura: int,
) -> ArtefatosExtracao:
    """Retorna os artefatos de uma legislatura específica."""

    return _artefatos(
        saida=pasta_saida / f"{prefixo_arquivo}_{id_legislatura}.json",
        estado=(
            Path("data/_estado/camara/deputados_por_legislatura")
            / f"id={id_legislatura}.state.json"
        ),
    )


def artefatos_despesa_deputado(
    pasta_dados: Path,
    nome_endpoint: str,
    deputado_id: str,
    ano: int,
) -> ArtefatosExtracao:
    """Retorna os artefatos de despesas de um deputado em um ano."""

    return _artefatos(
        saida=(
            pasta_dados
            / "despesas_deputados_federais"
            / str(ano)
            / f"despesas_{deputado_id}.json"
        ),
        estado=(
            Path("data/_estado/camara")
            / f"endpoint={nome_endpoint}"
            / f"ano={ano}"
            / f"id={deputado_id}.state.json"
        ),
    )
