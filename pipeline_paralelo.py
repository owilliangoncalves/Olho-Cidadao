"""Orquestra extracoes independentes em paralelo controlado.

Este módulo concentra os extratores que hoje podem rodar lado a lado sem
concorrer pelo mesmo conjunto de arquivos. Cada fonte continua mantendo suas
proprias regras internas de paginacao, retomada e rate limiting.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from configuracao.endpoint import obter_configuracao_endpoint
from configuracao.logger import logger
from configuracao.projeto import obter_parametros_pipeline
from configuracao.projeto import resolver_data_configurada
from extracao.ibge.localidades import ExtratorLocalidadesIBGE
from extracao.obrasgov.obras import ExtratorObrasGov
from extracao.pncp.consultas import ExtratorPNCPConsulta
from extracao.senado.senadores import ExtratorDadosSenado
from extracao.siconfi.api import ExtratorSiconfi
from extracao.siop.extrator import ExtratorSIOP
from extracao.transferegov.recursos import ExtratorTransferegovRecursos
from infra.errors import UserInputError
from pipeline import PipelineCamara


@dataclass(frozen=True)
class TarefaParalela:
    """Representa uma unidade independente de execucao do pipeline paralelo."""

    nome: str
    executar: Callable[[], None]


class PipelineParalelo:
    """Executa em paralelo os extratores que nao conflitam entre si.

    O foco aqui e agrupar fontes independentes em um unico comando sem misturar
    processos que compartilham os mesmos arquivos de saida. Fluxos que ainda
    exigem serializacao, como Portal da Transparencia, ANP e geometrias do
    ObrasGov, ficam fora deste pipeline.
    """

    def __init__(
        self,
        ano_inicio: int | None = None,
        ano_fim: int | None = None,
        pncp_data_inicial=None,
        pncp_data_final=None,
        max_workers: int | None = None,
        incluir_camara: bool | None = None,
        incluir_senado: bool | None = None,
        incluir_siop: bool | None = None,
        incluir_ibge: bool | None = None,
        incluir_pncp: bool | None = None,
        incluir_transferegov: bool | None = None,
        incluir_obrasgov: bool | None = None,
        incluir_siconfi: bool | None = None,
        senado_endpoint: str | None = None,
        ibge_datasets: list[str] | None = None,
        siconfi_recursos: list[str] | None = None,
        siconfi_filtros: dict | None = None,
        siconfi_tamanho_pagina: int | None = None,
    ):
        """Armazena os parametros de orquestracao do pipeline paralelo."""

        config = obter_parametros_pipeline("paralelo")
        fontes = config.get("fontes", {})

        self.ano_inicio = ano_inicio if ano_inicio is not None else config.get("ano_inicio")
        self.ano_fim = ano_fim if ano_fim is not None else config.get("ano_fim")
        self.pncp_data_inicial = (
            pncp_data_inicial
            if pncp_data_inicial is not None
            else resolver_data_configurada(config.get("pncp_data_inicial"))
        )
        self.pncp_data_final = (
            pncp_data_final
            if pncp_data_final is not None
            else resolver_data_configurada(config.get("pncp_data_final"))
        )
        resolved_max_workers = max_workers if max_workers is not None else config.get("max_workers")
        self.max_workers = resolved_max_workers
        self.incluir_camara = (
            incluir_camara if incluir_camara is not None else fontes.get("camara")
        )
        self.incluir_senado = (
            incluir_senado if incluir_senado is not None else fontes.get("senado")
        )
        self.incluir_siop = incluir_siop if incluir_siop is not None else fontes.get("siop")
        self.incluir_ibge = incluir_ibge if incluir_ibge is not None else fontes.get("ibge")
        self.incluir_pncp = incluir_pncp if incluir_pncp is not None else fontes.get("pncp")
        self.incluir_transferegov = (
            incluir_transferegov
            if incluir_transferegov is not None
            else fontes.get("transferegov")
        )
        self.incluir_obrasgov = (
            incluir_obrasgov if incluir_obrasgov is not None else fontes.get("obrasgov")
        )
        self.incluir_siconfi = (
            incluir_siconfi if incluir_siconfi is not None else fontes.get("siconfi")
        )
        self.senado_endpoint = (
            senado_endpoint if senado_endpoint is not None else config.get("senado_endpoint")
        )
        self.ibge_datasets = ibge_datasets if ibge_datasets is not None else config.get("ibge_datasets")
        self.siconfi_recursos = (
            siconfi_recursos if siconfi_recursos is not None else config.get("siconfi_recursos")
        )
        self.siconfi_filtros = (
            siconfi_filtros if siconfi_filtros is not None else config.get("siconfi_filtros")
        )
        self.siconfi_tamanho_pagina = (
            siconfi_tamanho_pagina
            if siconfi_tamanho_pagina is not None
            else config.get("siconfi_tamanho_pagina")
        )
        self._validar_precondicoes()

    def _validar_precondicoes(self):
        """Falha cedo quando a configuração do pipeline paralelo é inválida."""

        if self.ano_inicio is None or self.ano_fim is None:
            raise UserInputError(
                "O pipeline paralelo exige ano_inicio e ano_fim. "
                "Defina [config.pipelines.paralelo] no etl-config.toml "
                "ou informe --ano-inicio/--ano-fim."
            )

        if self.ano_inicio >= self.ano_fim:
            raise UserInputError(
                "ano_inicio deve ser menor que ano_fim no pipeline paralelo."
            )

        if self.pncp_data_inicial is None or self.pncp_data_final is None:
            raise UserInputError(
                "O pipeline paralelo exige pncp_data_inicial e pncp_data_final. "
                "Defina [config.pipelines.paralelo] no etl-config.toml "
                "ou informe --pncp-data-inicial/--pncp-data-final."
            )

        if self.pncp_data_inicial > self.pncp_data_final:
            raise UserInputError(
                "pncp_data_inicial nao pode ser maior que pncp_data_final."
            )

        if self.max_workers is None:
            raise UserInputError(
                "O pipeline paralelo exige max_workers. "
                "Defina [config.pipelines.paralelo].max_workers no etl-config.toml "
                "ou informe --max-workers."
            )

        if self.max_workers < 1:
            raise UserInputError("max_workers deve ser maior ou igual a 1.")

    def _tarefas(self) -> list[TarefaParalela]:
        """Monta a lista de tarefas independentes a executar em paralelo."""

        tarefas: list[TarefaParalela] = []

        if self.incluir_camara:
            tarefas.append(
                TarefaParalela(
                    nome="camara",
                    executar=lambda: PipelineCamara(
                        ano_inicio=self.ano_inicio,
                        ano_fim=self.ano_fim,
                    ).executar(),
                )
            )

        if self.incluir_senado:
            config = obter_configuracao_endpoint(self.senado_endpoint)
            tarefas.append(
                TarefaParalela(
                    nome="senado",
                    executar=lambda: ExtratorDadosSenado(
                        nome_endpoint=self.senado_endpoint,
                        configuracao=config,
                    ).executar(),
                )
            )

        if self.incluir_siop:
            tarefas.append(
                TarefaParalela(
                    nome="siop",
                    executar=lambda: ExtratorSIOP().executar(),
                )
            )

        if self.incluir_ibge:
            tarefas.append(
                TarefaParalela(
                    nome="ibge",
                    executar=lambda: ExtratorLocalidadesIBGE().executar(
                        datasets=self.ibge_datasets
                    ),
                )
            )

        if self.incluir_pncp:
            tarefas.append(
                TarefaParalela(
                    nome="pncp",
                    executar=lambda: ExtratorPNCPConsulta().executar(
                        data_inicial=self.pncp_data_inicial,
                        data_final=self.pncp_data_final,
                    ),
                )
            )

        if self.incluir_transferegov:
            tarefas.extend(
                [
                    TarefaParalela(
                        nome="transferegov_especial",
                        executar=lambda: ExtratorTransferegovRecursos(
                            grupo="especial"
                        ).executar(),
                    ),
                    TarefaParalela(
                        nome="transferegov_fundoafundo",
                        executar=lambda: ExtratorTransferegovRecursos(
                            grupo="fundoafundo"
                        ).executar(),
                    ),
                    TarefaParalela(
                        nome="transferegov_ted",
                        executar=lambda: ExtratorTransferegovRecursos(
                            grupo="ted"
                        ).executar(),
                    ),
                ]
            )

        if self.incluir_obrasgov:
            tarefas.append(
                TarefaParalela(
                    nome="obrasgov",
                    executar=lambda: ExtratorObrasGov().executar_recursos(),
                )
            )

        if self.incluir_siconfi:
            tarefas.append(
                TarefaParalela(
                    nome="siconfi",
                    executar=lambda: ExtratorSiconfi(
                        page_size=self.siconfi_tamanho_pagina
                    ).executar(
                        recursos=self.siconfi_recursos,
                        filtros=self.siconfi_filtros,
                    ),
                )
            )

        return tarefas

    def executar(self):
        """Executa o conjunto de tarefas com paralelismo limitado por módulo."""

        tarefas = self._tarefas()
        if not tarefas:
            logger.warning("[PARALELO] Nenhuma tarefa selecionada para execucao.")
            return

        concluidas: list[str] = []
        falhas: list[str] = []

        logger.info(
            "[PARALELO] Iniciando execucao | tarefas=%s | max_workers=%s",
            [tarefa.nome for tarefa in tarefas],
            min(self.max_workers, len(tarefas)),
        )

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tarefas))) as executor:
            future_map = {
                executor.submit(tarefa.executar): tarefa.nome
                for tarefa in tarefas
            }

            for future in as_completed(future_map):
                nome = future_map[future]
                try:
                    future.result()
                except Exception:
                    falhas.append(nome)
                    logger.exception("[PARALELO] Tarefa falhou | tarefa=%s", nome)
                else:
                    concluidas.append(nome)
                    logger.info("[PARALELO] Tarefa concluida | tarefa=%s", nome)

        logger.info(
            "[PARALELO] Execucao finalizada | concluidas=%s | falhas=%s",
            concluidas,
            falhas,
        )

        if falhas:
            raise RuntimeError(
                "Falha em uma ou mais tarefas do pipeline paralelo: "
                + ", ".join(sorted(falhas))
            )
