"""Helpers puros de leitura e normalização para deputados federais."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from datetime import datetime
from pathlib import Path

from utils.documentos import base_cnpj
from utils.documentos import normalizar_documento
from utils.documentos import tipo_documento


def iterar_ids_legislaturas(arquivo_entrada: Path) -> Iterator[int]:
    """Lê o arquivo mestre de legislaturas e devolve apenas IDs válidos."""

    if not arquivo_entrada.exists():
        return

    with open(arquivo_entrada, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue

            try:
                registro = json.loads(linha)
            except json.JSONDecodeError:
                continue

            legislatura_id = registro.get("id")
            if legislatura_id is not None:
                yield legislatura_id


def carregar_intervalos_legislaturas(caminho: Path) -> dict[int, tuple[date, date]]:
    """Carrega as janelas temporais conhecidas de cada legislatura."""

    legislaturas: dict[int, tuple[date, date]] = {}
    if not caminho.exists():
        return legislaturas

    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue

            try:
                registro = json.loads(linha)
            except json.JSONDecodeError:
                continue

            legislatura_id = registro.get("id")
            data_inicio = registro.get("dataInicio")
            data_fim = registro.get("dataFim")
            if legislatura_id is None or not data_inicio or not data_fim:
                continue

            legislaturas[legislatura_id] = (
                datetime.strptime(data_inicio, "%Y-%m-%d").date(),
                datetime.strptime(data_fim, "%Y-%m-%d").date(),
            )

    return legislaturas


def anos_no_intervalo_legislatura(
    id_legislatura: int,
    legislaturas: dict[int, tuple[date, date]],
    periodo_inicio: date,
    periodo_fim: date,
) -> list[int]:
    """Retorna os anos em que legislatura e janela pedida se cruzam."""

    intervalo = legislaturas.get(id_legislatura)
    if intervalo is None:
        return []

    inicio_legislatura, fim_legislatura = intervalo
    inicio = max(inicio_legislatura, periodo_inicio)
    fim = min(fim_legislatura, periodo_fim)
    if inicio > fim:
        return []

    return list(range(inicio.year, fim.year + 1))


def _arquivos_deputados(caminho_pai: Path) -> list[Path]:
    """Normaliza o modo de leitura do insumo pai em lista ordenada de arquivos."""

    if caminho_pai.is_dir():
        return sorted(
            caminho_pai.glob("*.json"),
            key=lambda path: int(path.stem.split("_")[-1]),
            reverse=True,
        )
    return [caminho_pai]


def iterar_trabalhos_despesas(
    caminho_pai: Path,
    campo_id: str,
    legislaturas: dict[int, tuple[date, date]],
    periodo_inicio: date,
    periodo_fim: date,
) -> Iterator[tuple[str, int, dict]]:
    """Gera trabalhos de despesas sem materializar toda a fila em memória."""

    if not caminho_pai.exists():
        return

    vistos: set[tuple[str, int]] = set()
    for arquivo in _arquivos_deputados(caminho_pai):
        with open(arquivo, encoding="utf-8") as origem:
            for linha in origem:
                try:
                    registro = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                deputado_id = registro.get(campo_id)
                id_legislatura = registro.get("id_legislatura") or registro.get("idLegislatura")
                if deputado_id is None or id_legislatura is None:
                    continue

                anos = anos_no_intervalo_legislatura(
                    id_legislatura,
                    legislaturas,
                    periodo_inicio,
                    periodo_fim,
                )
                for ano in sorted(anos, reverse=True):
                    chave = (str(deputado_id), ano)
                    if chave in vistos:
                        continue

                    vistos.add(chave)
                    yield str(deputado_id), ano, {
                        "id_legislatura": id_legislatura,
                        "nome": registro.get("nome"),
                        "sigla_uf": registro.get("siglaUf"),
                        "sigla_partido": registro.get("siglaPartido"),
                        "uri": registro.get("uri"),
                    }


def enriquecer_registro_despesa(
    dado: dict,
    *,
    deputado_id: str,
    ano: int,
    nome_endpoint: str,
    contexto_deputado: dict,
) -> dict:
    """Adiciona contexto do deputado e campos derivados do fornecedor."""

    registro = dict(dado)
    registro["id_deputado"] = deputado_id
    registro["ano_arquivo"] = ano

    id_legislatura = contexto_deputado.get("id_legislatura")
    if id_legislatura is not None:
        registro["id_legislatura"] = id_legislatura
    if contexto_deputado.get("nome"):
        registro["nome_deputado"] = contexto_deputado["nome"]
    if contexto_deputado.get("sigla_uf"):
        registro["sigla_uf_deputado"] = contexto_deputado["sigla_uf"]
    if contexto_deputado.get("sigla_partido"):
        registro["sigla_partido_deputado"] = contexto_deputado["sigla_partido"]
    if contexto_deputado.get("uri"):
        registro["uri_deputado"] = contexto_deputado["uri"]

    documento = normalizar_documento(registro.get("cnpjCpfFornecedor"))
    registro["documento_fornecedor_normalizado"] = documento
    registro["tipo_documento_fornecedor"] = tipo_documento(documento)
    registro["cnpj_base_fornecedor"] = base_cnpj(documento)
    registro["orgao_origem"] = "camara"
    registro["endpoint_origem"] = nome_endpoint
    return registro
