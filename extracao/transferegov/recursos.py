"""Extratores genéricos para as APIs do ecossistema Transferegov."""

from __future__ import annotations

from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.publica.base import ExtratorAPIPublicaBase
from utils.filtros import slug_filtros

RESOURCE_GROUPS = {
    "especial": [
        "programa_especial",
        "plano_acao_especial",
        "executor_especial",
        "empenho_especial",
        "ordem_pagamento_ordem_bancaria_especial",
        "historico_pagamento_especial",
    ],
    "fundoafundo": [
        "programa",
        "plano_acao",
        "empenho",
        "relatorio_gestao",
    ],
    "ted": [
        "programa",
        "plano_acao",
        "termo_execucao",
        "nota_credito",
        "programacao_financeira",
        "trf",
    ],
}

ORGAO_MAP = {
    "especial": "transferegov_especial",
    "fundoafundo": "transferegov_fundoafundo",
    "ted": "transferegov_ted",
}


class ExtratorTransferegovRecursos(ExtratorAPIPublicaBase):
    """Extrai datasets paginados das APIs do Transferegov."""

    def __init__(self, grupo: str, page_size: int | None = None):
        """Configura o grupo de API e o tamanho de página base."""

        config = obter_parametros_extrator("transferegov")
        super().__init__(
            orgao=ORGAO_MAP[grupo],
            nome_endpoint=grupo,
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
        self.grupo = grupo
        self.page_size = page_size if page_size is not None else config.get("page_size")

    def executar(self, recursos: list[str] | None = None, filtros: dict | None = None):
        """Extrai os recursos solicitados do grupo configurado."""

        recursos_selecionados = recursos or RESOURCE_GROUPS[self.grupo]
        assinatura = slug_filtros(filtros)

        for recurso in recursos_selecionados:
            resumo = self._executar_tarefa_paginada(
                endpoint=f"/{recurso}",
                base_params=filtros or {},
                relative_output_path=(
                    Path("transferegov")
                    / self.grupo
                    / recurso
                    / f"consulta={assinatura}.json"
                ),
                context={
                    "dataset": recurso,
                    "grupo_api": self.grupo,
                    "filtros": filtros or {},
                },
                pagination={
                    "style": "offset",
                    "offset_param": "offset",
                    "limit_param": "limit",
                    "page_size": self.page_size,
                    "start_offset": 0,
                },
            )

            self.logger.info(
                "[TRANSFEREGOV] Recurso concluido | grupo=%s | recurso=%s | status=%s | registros=%s",
                self.grupo,
                recurso,
                resumo["status"],
                resumo["records"],
            )
