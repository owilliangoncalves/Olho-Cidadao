"""Pacote PNCP com fachada pública e orquestração concentradas aqui."""

from __future__ import annotations

from functools import cache
from typing import Any

from configuracao import obter_url_endpoint
from extracao.pncp.config import MONTHLY_RESOURCES
from extracao.pncp.config import PNCP_PAGINACAO
from extracao.pncp.config import PNCPConsultaConfig
from extracao.pncp.tarefas import iterar_anos
from extracao.pncp.tarefas import iterar_janelas_mensais
from extracao.pncp.tarefas import output_path_janela
from extracao.pncp.tarefas import output_path_pca
from infra.errors import UserInputError


@cache
def _construir_pncp_consulta():
    """Cria e memoriza o orquestrador público do pacote."""

    from extracao.publica import ExtratorAPIPublicaBase

    class PNCPConsulta(ExtratorAPIPublicaBase):
        """Extrai contratos, atas e PCA da API pública do PNCP."""

        def __init__(self, page_size: int | None = None):
            self.cfg = PNCPConsultaConfig.carregar(page_size=page_size)
            super().__init__(
                orgao="pncp",
                nome_endpoint="consulta_publica",
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )

        def _executar_janela(self, resource: str, endpoint: str, data_inicial, data_final):
            """Executa uma janela mensal para contratos ou atas."""

            resumo = self._executar_tarefa_paginada(
                endpoint=endpoint,
                base_params={
                    "dataInicial": data_inicial.strftime("%Y%m%d"),
                    "dataFinal": data_final.strftime("%Y%m%d"),
                },
                relative_output_path=output_path_janela(resource, data_inicial),
                context={
                    "dataset": resource,
                    "data_inicial": data_inicial.isoformat(),
                    "data_final": data_final.isoformat(),
                },
                pagination={**PNCP_PAGINACAO, "page_size": self.cfg.page_size},
            )
            self.logger.info(
                "[PNCP] Janela concluida | recurso=%s | inicio=%s | fim=%s | status=%s | registros=%s",
                resource,
                data_inicial,
                data_final,
                resumo["status"],
                resumo["records"],
            )
            return resumo

        def _executar_pca(self, ano: int, codigo_classificacao_superior: str | None):
            """Executa a extração anual do PCA."""

            params = {"anoPca": ano}
            if codigo_classificacao_superior is not None:
                params["codigoClassificacaoSuperior"] = codigo_classificacao_superior

            resumo = self._executar_tarefa_paginada(
                endpoint=obter_url_endpoint("pncp_pca"),
                base_params=params,
                relative_output_path=output_path_pca(ano),
                context={
                    "dataset": "pca",
                    "ano_pca": ano,
                    "codigo_classificacao_superior": codigo_classificacao_superior,
                },
                pagination={**PNCP_PAGINACAO, "page_size": self.cfg.page_size},
            )
            self.logger.info(
                "[PNCP] PCA concluido | ano=%s | status=%s | registros=%s",
                ano,
                resumo["status"],
                resumo["records"],
            )
            return resumo

        def executar(
            self,
            data_inicial,
            data_final,
            incluir_contratos: bool = True,
            incluir_atas: bool = True,
            incluir_pca: bool = True,
            codigo_classificacao_superior: str | None = None,
        ):
            """Executa as consultas do PNCP para o intervalo informado."""

            if data_inicial > data_final:
                raise UserInputError("data_inicial não pode ser maior que data_final no PNCP.")

            if incluir_contratos:
                endpoint = obter_url_endpoint(MONTHLY_RESOURCES["contratos"])
                for inicio, fim in iterar_janelas_mensais(data_inicial, data_final):
                    self._executar_janela("contratos", endpoint, inicio, fim)

            if incluir_atas:
                endpoint = obter_url_endpoint(MONTHLY_RESOURCES["atas"])
                for inicio, fim in iterar_janelas_mensais(data_inicial, data_final):
                    self._executar_janela("atas", endpoint, inicio, fim)

            if incluir_pca:
                for ano in iterar_anos(data_inicial, data_final):
                    self._executar_pca(ano, codigo_classificacao_superior)

    PNCPConsulta.__module__ = __name__
    return PNCPConsulta


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "PNCPConsulta":
        consulta = _construir_pncp_consulta()
        globals()[name] = consulta
        return consulta
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantém introspecção consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "MONTHLY_RESOURCES",
    "PNCPConsulta",
    "PNCPConsultaConfig",
    "PNCP_PAGINACAO",
]
