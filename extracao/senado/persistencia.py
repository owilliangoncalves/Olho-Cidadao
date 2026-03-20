"""Persistencia anual dos registros de despesas do Senado."""

from __future__ import annotations

import json

from extracao.senado.arquivos import SenadoArquivosAno
from extracao.senado.dados import enriquecer_registro_senado
from infra.estado.arquivos import limpar_artefatos


def salvar_despesas_ano(
    arquivos: SenadoArquivosAno,
    registros,
    *,
    ano: int,
    nome_endpoint: str,
    logger,
    orgao: str,
) -> int:
    """Grava o resultado do ano em arquivo temporario e promove no final."""

    if arquivos.temporario.exists():
        arquivos.temporario.unlink()

    total = 0
    try:
        with open(arquivos.temporario, "w", encoding="utf-8") as handle:
            for item in registros:
                json.dump(
                    enriquecer_registro_senado(item, ano=ano, nome_endpoint=nome_endpoint),
                    handle,
                    ensure_ascii=False,
                )
                handle.write("\n")
                total += 1

        if total == 0:
            limpar_artefatos(arquivos.temporario)
            return 0

        arquivos.temporario.replace(arquivos.saida)
        logger.info(
            "[%s] Arquivo salvo em: %s | registros=%s",
            orgao,
            arquivos.saida,
            total,
        )
        return total
    except Exception:
        limpar_artefatos(arquivos.temporario)
        raise
