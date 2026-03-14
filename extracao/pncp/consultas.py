"""Extratores de consulta pública do PNCP."""

from __future__ import annotations

from datetime import date
from datetime import timedelta
from pathlib import Path

from configuracao.endpoint import obter_url_endpoint
from configuracao.projeto import obter_parametros_extrator
from extracao.publica.base import ExtratorAPIPublicaBase


def _fim_do_mes(inicio: date) -> date:
    """Retorna a data final do mês da data informada."""

    proximo_mes = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
    return proximo_mes - timedelta(days=1)


class ExtratorPNCPConsulta(ExtratorAPIPublicaBase):
    """Extrai contratos, atas e PCA da API pública do PNCP."""

    def __init__(self, page_size: int | None = None):
        """Configura a taxa e o tamanho de página padrão do PNCP."""

        config = obter_parametros_extrator("pncp")
        super().__init__(
            orgao="pncp",
            nome_endpoint="consulta_publica",
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
        resolved_page_size = page_size if page_size is not None else config.get("page_size")
        self.page_size = max(10, resolved_page_size)

    def _iterar_janelas_mensais(self, data_inicial: date, data_final: date):
        """Divide um intervalo de datas em janelas mensais fechadas."""

        cursor = data_inicial.replace(day=1)
        while cursor <= data_final:
            inicio = max(cursor, data_inicial)
            fim = min(_fim_do_mes(cursor), data_final)
            yield inicio, fim
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    def _endpoint(self, nome_endpoint: str) -> str:
        """Retorna o caminho do endpoint configurado em `etl-config.toml`."""

        return obter_url_endpoint(nome_endpoint)

    def _executar_janela(self, resource: str, endpoint: str, data_inicial: date, data_final: date):
        """Executa uma janela mensal para contratos ou atas."""

        resumo = self._executar_tarefa_paginada(
            endpoint=endpoint,
            base_params={
                "dataInicial": data_inicial.strftime("%Y%m%d"),
                "dataFinal": data_final.strftime("%Y%m%d"),
            },
            relative_output_path=(
                Path("pncp")
                / resource
                / f"ano={data_inicial.year}"
                / f"mes={data_inicial.month:02d}.json"
            ),
            context={
                "dataset": resource,
                "data_inicial": data_inicial.isoformat(),
                "data_final": data_final.isoformat(),
            },
            pagination={
                "style": "page",
                "page_param": "pagina",
                "page_size_param": "tamanhoPagina",
                "page_size": self.page_size,
                "start_page": 1,
            },
        )

        self.logger.info(
            "[PNCP] Janela concluida | recurso=%s | inicio=%s | fim=%s | status=%s | registros=%s",
            resource,
            data_inicial,
            data_final,
            resumo["status"],
            resumo["records"],
        )

    def executar(
        self,
        data_inicial: date,
        data_final: date,
        incluir_contratos: bool = True,
        incluir_atas: bool = True,
        incluir_pca: bool = True,
        codigo_classificacao_superior: str | None = None,
    ):
        """Executa as consultas do PNCP para o intervalo informado."""

        if incluir_contratos:
            endpoint = self._endpoint("pncp_contratos")
            for inicio, fim in self._iterar_janelas_mensais(data_inicial, data_final):
                self._executar_janela("contratos", endpoint, inicio, fim)

        if incluir_atas:
            endpoint = self._endpoint("pncp_atas")
            for inicio, fim in self._iterar_janelas_mensais(data_inicial, data_final):
                self._executar_janela("atas", endpoint, inicio, fim)

        if incluir_pca:
            endpoint = self._endpoint("pncp_pca")
            for ano in range(data_inicial.year, data_final.year + 1):
                params = {"anoPca": ano}
                if codigo_classificacao_superior is not None:
                    params["codigoClassificacaoSuperior"] = codigo_classificacao_superior

                resumo = self._executar_tarefa_paginada(
                    endpoint=endpoint,
                    base_params=params,
                    relative_output_path=Path("pncp") / "pca" / f"ano={ano}.json",
                    context={
                        "dataset": "pca",
                        "ano_pca": ano,
                        "codigo_classificacao_superior": codigo_classificacao_superior,
                    },
                    pagination={
                        "style": "page",
                        "page_param": "pagina",
                        "page_size_param": "tamanhoPagina",
                        "page_size": self.page_size,
                        "start_page": 1,
                    },
                )

                self.logger.info(
                    "[PNCP] PCA concluido | ano=%s | status=%s | registros=%s",
                    ano,
                    resumo["status"],
                    resumo["records"],
                )
