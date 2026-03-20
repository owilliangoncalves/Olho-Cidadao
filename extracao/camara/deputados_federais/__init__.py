"""Orquestração da extração de deputados federais da Câmara.

O pacote expõe três fluxos públicos:
- `Legislatura`: baixa a lista mestre de legislaturas;
- `DeputadosLegislatura`: expande deputados por legislatura;
- `Despesas`: consulta despesas por deputado e por ano.

As responsabilidades de configuração, artefatos, leitura de dados e paginação
ficam em módulos auxiliares. A orquestração pública permanece aqui.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from threading import local

from configuracao import obter_configuracao_endpoint
from extracao.extrator_da_base import ExtratorBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas
from infra.estado.checkpoints import CheckpointStore
from infra.http.cliente import http_client
from infra.http.sessao import criar_sessao

from .artefatos import artefatos_deputados_legislatura
from .artefatos import artefatos_despesa_deputado
from .artefatos import artefatos_legislaturas
from .config import DEPUTADOS_REQUIRED_KEYS
from .config import DESPESAS_REQUIRED_KEYS
from .config import LEGISLATURAS_REQUIRED_KEYS
from .config import DeputadosLegislaturaConfig
from .config import DespesasConfig
from .config import LegislaturasConfig
from .dados import carregar_intervalos_legislaturas
from .dados import enriquecer_registro_despesa
from .dados import iterar_ids_legislaturas
from .dados import iterar_trabalhos_despesas
from .paginado import executar_jsonl_paginado
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.paginacao import proxima_pagina

_thread_local = local()


def _sessao_da_thread():
    """Retorna uma sessão HTTP reutilizável por thread."""

    if not hasattr(_thread_local, "session"):
        _thread_local.session = criar_sessao()
    return _thread_local.session


class _ExtratorDespesaDeputado(ExtratorBase):
    """Executa a unidade de trabalho de despesas de um deputado em um ano."""

    def __init__(self, cfg: DespesasConfig, configuracao: dict, session=None):
        super().__init__("camara")
        self.cfg = cfg
        self.configuracao = configuracao
        self.endpoint = configuracao["endpoint"]
        self.paginacao = bool(configuracao["paginacao"])
        self.session = session

    def _preparar_parametros(self) -> dict:
        """Monta os parâmetros iniciais da requisição."""

        params = dict(self.configuracao.get("params") or {})
        params["itens"] = self.configuracao["itens"]
        return params

    def _fazer_requisicao(self, url: str, params: dict | None):
        """Executa a chamada HTTP com limites próprios do endpoint de despesas."""

        return http_client.get(
            url=url,
            params=params,
            session=self.session,
            timeout=(10, 60),
            rate_key=f"CAMARA:{self.cfg.nome_endpoint}",
            rate_limit_per_sec=self.cfg.rate_limit_per_sec,
            max_rate_per_sec=self.cfg.max_rate_per_sec,
        )

    def _enriquecer_registro(self, dado: dict) -> dict:
        """Adiciona contexto do deputado e chaves derivadas do fornecedor."""

        return enriquecer_registro_despesa(
            dado,
            deputado_id=str(self.configuracao["contexto_id"]),
            ano=int(self.configuracao["contexto_ano"]),
            nome_endpoint=self.cfg.nome_endpoint,
            contexto_deputado=self.configuracao.get("contexto_deputado") or {},
        )

    def executar(
        self,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Extrai todas as páginas de despesas da unidade `(deputado, ano)`."""

        deputado_id = str(self.configuracao["contexto_id"])
        ano = int(self.configuracao["contexto_ano"])
        artefatos = artefatos_despesa_deputado(
            self.cfg.pasta_dados,
            self.cfg.nome_endpoint,
            deputado_id,
            ano,
        )
        return executar_jsonl_paginado(
            extrator=self,
            artefatos=artefatos,
            required_output_keys=DESPESAS_REQUIRED_KEYS,
            initial_url=f"{self.base_url}{self.endpoint}",
            initial_params=self._preparar_parametros(),
            fetch_page=self._fazer_requisicao,
            extract_items=lambda resposta: resposta.get("dados", []),
            transform_item=self._enriquecer_registro,
            empty_context=f"{self.cfg.nome_endpoint}:{artefatos.saida}",
            log_page=lambda pagina, itens: self.logger.info(
                "Página extraída | deputado=%s | ano=%s | pagina=%s | registros=%s",
                deputado_id,
                ano,
                pagina,
                len(itens),
            ),
            next_url_from_response=(
                lambda resposta: None if not self.paginacao else proxima_pagina(resposta)
            ),
            allow_empty_retry=_allow_empty_retry,
            from_empty_retry=_from_empty_retry,
        )


class Legislatura(ExtratorBase):
    """Baixa a lista mestre de legislaturas da Câmara."""

    def __init__(self, arquivo_saida: str | None = None):
        super().__init__("camara")
        self.cfg = LegislaturasConfig.carregar(arquivo_saida=arquivo_saida)

    def executar(
        self,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Percorre o endpoint de legislaturas com retomada por artefatos."""

        self.logger.info("Iniciando extração da lista mestre de legislaturas.")
        resumo = executar_jsonl_paginado(
            extrator=self,
            artefatos=artefatos_legislaturas(self.cfg.arquivo_saida),
            required_output_keys=LEGISLATURAS_REQUIRED_KEYS,
            initial_url=f"{self.base_url}{self.cfg.endpoint}",
            initial_params={"itens": self.cfg.itens},
            fetch_page=lambda url, params: self._fazer_requisicao(url, params=params, delay=0),
            extract_items=lambda resposta: resposta.get("dados", []),
            transform_item=lambda registro: registro,
            empty_context="camara:legislaturas",
            log_page=lambda pagina, _itens: self.logger.info(
                "Legislaturas - extraindo página %s",
                pagina,
            ),
            allow_empty_retry=_allow_empty_retry,
            from_empty_retry=_from_empty_retry,
        )
        if resumo["status"] == "success":
            self.logger.info("Lista de legislaturas baixada com sucesso.")
        elif resumo["status"] == "empty":
            self.logger.warning("Nenhuma legislatura encontrada.")
        return resumo


class DeputadosLegislatura(ExtratorBase):
    """Baixa os deputados vinculados a cada legislatura conhecida."""

    def __init__(
        self,
        arquivo_entrada: str | None = None,
        pasta_saida: str | None = None,
        prefixo_arquivo: str | None = None,
    ):
        super().__init__("camara")
        self.cfg = DeputadosLegislaturaConfig.carregar(
            arquivo_entrada=arquivo_entrada,
            pasta_saida=pasta_saida,
            prefixo_arquivo=prefixo_arquivo,
        )

    def _processar_legislatura(
        self,
        id_legislatura: int,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Extrai todas as páginas de deputados de uma legislatura."""

        endpoint = self.cfg.endpoint.format(id=id_legislatura)
        artefatos = artefatos_deputados_legislatura(
            self.cfg.pasta_saida,
            self.cfg.prefixo_arquivo,
            id_legislatura,
        )
        return executar_jsonl_paginado(
            extrator=self,
            artefatos=artefatos,
            required_output_keys=DEPUTADOS_REQUIRED_KEYS,
            initial_url=f"{self.base_url}{endpoint}",
            initial_params={"itens": self.cfg.itens},
            fetch_page=lambda url, params: self._fazer_requisicao(url, params=params, delay=0),
            extract_items=lambda resposta: resposta.get("dados", []),
            transform_item=lambda registro: {**registro, "id_legislatura": id_legislatura},
            empty_context=f"deputados_legislatura:{id_legislatura}",
            log_page=lambda pagina, _itens: self.logger.info(
                "Legislatura %s - página %s",
                id_legislatura,
                pagina,
            ),
            allow_empty_retry=_allow_empty_retry,
            from_empty_retry=_from_empty_retry,
        )

    def executar(self):
        """Processa todas as legislaturas com concorrência controlada."""

        if not self.cfg.arquivo_entrada.exists():
            self.logger.error("Arquivo não encontrado: %s", self.cfg.arquivo_entrada)
            return

        self.logger.info("Iniciando extração de deputados por legislatura.")
        enviados = executar_tarefas_limitadas(
            iterar_ids_legislaturas(self.cfg.arquivo_entrada),
            self._processar_legislatura,
            max_workers=self.cfg.max_workers,
            max_pending=self.cfg.max_pending,
        )

        if enviados == 0:
            self.logger.warning("Nenhuma legislatura encontrada.")
            return

        self.logger.info("Processo de extração finalizado com sucesso.")


class Despesas(ExtratorBase):
    """Expande deputados em tarefas dependentes, como despesas por ano."""

    def __init__(self, nome_endpoint: str, configuracao: dict, pasta_dados: str = "data"):
        super().__init__("camara")
        self.cfg = DespesasConfig.carregar(
            nome_endpoint,
            configuracao,
            pasta_dados=pasta_dados,
        )
        self.endpoint_config = configuracao
        self.caminho_pai = (
            self.cfg.pasta_dados
            / obter_configuracao_endpoint(self.cfg.endpoint_pai)["salvar_como"]
        )
        self.checkpoints = CheckpointStore()
        self.stats = ContadorExecucao()

    def _arquivo_saida(self, deputado_id: str, ano: int) -> Path:
        """Retorna o arquivo final esperado para `(deputado, ano)`."""

        return artefatos_despesa_deputado(
            self.cfg.pasta_dados,
            self.cfg.nome_endpoint,
            deputado_id,
            ano,
        ).saida

    def _iterar_trabalhos(self, ano_inicio: int, ano_fim: int):
        """Gera as tarefas válidas respeitando a janela temporal pedida."""

        if not self.caminho_pai.exists():
            self.logger.warning("Caminho pai nao encontrado: %s", self.caminho_pai)
            return

        legislaturas = carregar_intervalos_legislaturas(self.cfg.pasta_dados / "legislaturas.json")
        periodo_inicio = date(ano_inicio, 1, 1)
        periodo_fim = date(ano_fim - 1, 12, 31)
        yield from iterar_trabalhos_despesas(
            self.caminho_pai,
            self.cfg.campo_id,
            legislaturas,
            periodo_inicio,
            periodo_fim,
        )

    def _reutilizar_saida_final(self, deputado_id: str, ano: int) -> bool:
        """Reaproveita arquivos íntegros já existentes e registra checkpoint."""

        contexto = str(ano)
        endpoint = self.cfg.nome_endpoint
        if self.checkpoints.get_status(endpoint, deputado_id, contexto) is not None:
            return False

        caminho_saida = self._arquivo_saida(deputado_id, ano)

        if not caminho_saida.exists() or caminho_saida.stat().st_size == 0:
            return False
        if not arquivo_jsonl_tem_chaves(caminho_saida, DESPESAS_REQUIRED_KEYS):
            return False

        self.checkpoints.mark_success(
            endpoint=endpoint,
            entity_id=deputado_id,
            context=contexto,
            records=-1,
            pages=0,
            message="arquivo final reutilizado",
        )
        self.stats.increment("skipped")
        return True

    def _executar_tarefa(self, deputado_id: str, ano: int, contexto_deputado: dict):
        """Executa a unidade `(deputado, ano)` com checkpoint por tarefa."""

        endpoint = self.cfg.nome_endpoint
        contexto = str(ano)

        if self.checkpoints.is_terminal(endpoint, deputado_id, contexto) and arquivo_jsonl_tem_chaves(
            self._arquivo_saida(deputado_id, ano),
            DESPESAS_REQUIRED_KEYS,
        ):
            self.stats.increment("skipped")
            return

        if self._reutilizar_saida_final(deputado_id, ano):
            return

        self.checkpoints.mark_running(endpoint, deputado_id, contexto)

        try:
            resumo = _ExtratorDespesaDeputado(
                self.cfg,
                {
                    **self.endpoint_config,
                    "endpoint": self.cfg.endpoint_template.replace("{id}", deputado_id),
                    "params": {"ano": ano},
                    "contexto_id": deputado_id,
                    "contexto_ano": ano,
                    "contexto_deputado": contexto_deputado,
                },
                session=_sessao_da_thread(),
            ).executar()

            if resumo["status"] == "skipped":
                self.checkpoints.mark_success(
                    endpoint=endpoint,
                    entity_id=deputado_id,
                    context=contexto,
                    records=-1,
                    pages=0,
                    message="arquivo final reutilizado",
                )
                self.stats.increment("skipped")
                return

            if resumo["status"] == "skipped_empty":
                self.checkpoints.mark_empty(
                    endpoint=endpoint,
                    entity_id=deputado_id,
                    context=contexto,
                    pages=0,
                )
                self.stats.increment("skipped")
                return

            if resumo["records"] == 0:
                self.checkpoints.mark_empty(
                    endpoint=endpoint,
                    entity_id=deputado_id,
                    context=contexto,
                    pages=int(resumo["pages"]),
                )
                self.stats.increment("empty")
                return

            self.checkpoints.mark_success(
                endpoint=endpoint,
                entity_id=deputado_id,
                context=contexto,
                records=int(resumo["records"]),
                pages=int(resumo["pages"]),
            )
            self.stats.increment("completed")
            self.logger.info(
                "Concluido | deputado=%s | ano=%s | paginas=%s | registros=%s",
                deputado_id,
                ano,
                resumo["pages"],
                resumo["records"],
            )
        except Exception as exc:
            self.checkpoints.mark_error(endpoint, deputado_id, contexto, str(exc))
            self.stats.increment("failed")
            self.logger.exception("Falha | deputado=%s | ano=%s", deputado_id, ano)

    def executar(self, ano_inicio: int = 2000, ano_fim: int = 2027):
        """Executa o crawler dependente para o intervalo de anos informado."""

        started_at = time.time()
        self.logger.info("Crawler iniciado | anos=%s-%s", ano_inicio, ano_fim)
        enviados = executar_tarefas_limitadas(
            self._iterar_trabalhos(ano_inicio, ano_fim),
            self._executar_tarefa,
            max_workers=self.cfg.max_workers,
            max_pending=self.cfg.max_pending,
        )

        if enviados == 0:
            self.logger.warning("Nenhum ID encontrado para alimentar %s", self.cfg.nome_endpoint)
            return

        elapsed = time.time() - started_at
        stats = self.stats.snapshot()
        self.logger.info(
            "Crawler finalizado | tempo=%.2fs | concluidos=%s | vazios=%s | pulados=%s | falhas=%s",
            elapsed,
            stats["completed"],
            stats["empty"],
            stats["skipped"],
            stats["failed"],
        )


__all__ = [
    "DeputadosLegislatura",
    "Despesas",
    "Legislatura",
]
