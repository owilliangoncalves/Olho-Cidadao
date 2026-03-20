"""Helpers puros de tarefas, filtros e caminhos do Portal."""

from __future__ import annotations

from pathlib import Path

from extracao.portal.config import PORTAL_OUTPUT_ROOT


def contador_por_status(status: str | None) -> str:
    """Normaliza o status resumido para o contador agregado."""

    if status == "success":
        return "completed"
    if status in {"skipped", "skipped_empty"}:
        return "skipped"
    return "empty"


def documento_tem_cnpj(documento: str | None) -> bool:
    """Indica se o documento informado tem formato de CNPJ limpo."""

    return bool(documento) and len(documento) == 14


def filtrar_anos(
    anos: list[int] | tuple[int, ...],
    *,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
) -> list[int]:
    """Aplica o recorte anual configurado sobre uma lista de anos."""

    return [
        ano
        for ano in anos
        if (ano_inicio is None or ano >= ano_inicio)
        and (ano_fim is None or ano < ano_fim)
    ]


def gerar_tarefas_documentos(
    fornecedores,
    fases: list[int],
    *,
    ano_inicio: int | None = None,
    ano_fim: int | None = None,
) -> list[tuple[str, int, int]]:
    """Expande fornecedores em tarefas de documentos ordenadas para execucao."""

    tarefas: list[tuple[str, int, int]] = []
    for fornecedor in fornecedores or []:
        documento = fornecedor["documento"]
        anos = filtrar_anos(
            fornecedor.get("anos", []),
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
        )
        for ano in anos:
            for fase in fases:
                tarefas.append((documento, ano, fase))

    return sorted(tarefas, key=lambda item: (item[1], item[2], item[0]), reverse=True)


def iterar_tarefas_sancoes(endpoints: dict[str, str], documentos):
    """Gera combinacoes de dataset, endpoint e documento para sancoes."""

    for dataset, endpoint in endpoints.items():
        for documento in documentos:
            yield (dataset, endpoint, documento)


def params_sancao(dataset: str, documento: str) -> dict | None:
    """Resolve os parametros corretos para cada dataset de sancoes."""

    if dataset in {"ceis", "cnep"}:
        return {"codigoSancionado": documento}
    if dataset == "cepim" and documento_tem_cnpj(documento):
        return {"cnpjSancionado": documento}
    return None


def output_path_documentos(documento: str, ano: int, fase: int) -> Path:
    """Deriva o caminho relativo de saida para documentos por favorecido."""

    return (
        PORTAL_OUTPUT_ROOT
        / "documentos_por_favorecido"
        / f"ano={ano}"
        / f"fase={fase}"
        / f"fornecedor={documento}.json"
    )


def output_path_notas_fiscais(documento: str) -> Path:
    """Deriva o caminho relativo de saida para notas fiscais."""

    return PORTAL_OUTPUT_ROOT / "notas_fiscais" / f"fornecedor={documento}.json"


def output_path_sancao(dataset: str, documento: str) -> Path:
    """Deriva o caminho relativo de saida para um dataset de sancoes."""

    return PORTAL_OUTPUT_ROOT / "sancoes" / dataset / f"fornecedor={documento}.json"

