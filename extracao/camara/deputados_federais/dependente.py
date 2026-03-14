"""Extrai endpoints dependentes da Câmara a partir da base de deputados."""

import json
import time
from datetime import date, datetime
from pathlib import Path
from threading import local

from configuracao.endpoint import urls
from extracao.camara.deputados_federais.camara import ExtratorDadosCamara
from extracao.extrator_da_base import ExtratorBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas
from infra.estado.checkpoints import CheckpointStore
from infra.http.sessao import criar_sessao
from utils.jsonl import arquivo_jsonl_tem_chaves

_thread_local = local()


def get_session():
    """Retorna uma sessão HTTP exclusiva da thread atual."""

    if not hasattr(_thread_local, "session"):
        _thread_local.session = criar_sessao()
    return _thread_local.session


class ExtratorDependente(ExtratorBase):
    """Expande deputados em tarefas dependentes, como despesas por ano.

    A classe combina:

    - leitura progressiva dos arquivos de deputados;
    - filtragem por legislatura e janela de anos;
    - checkpoint por unidade `(endpoint, entidade, contexto)`;
    - concorrência limitada para controlar memória e pressão na API.
    """

    def __init__(self, nome_endpoint: str, configuracao: dict, pasta_dados="data"):
        """Configura o extrator dependente e o armazenamento de estado."""

        super().__init__("camara")

        self.nome_endpoint = nome_endpoint
        self.configuracao = configuracao
        self.pasta_dados = Path(pasta_dados)
        self.endpoint_template = configuracao["endpoint"]
        self.endpoint_pai = configuracao["depende_de"]
        self.campo_id = configuracao.get("campo_id", "id")

        arquivo = urls["endpoints"][self.endpoint_pai]["salvar_como"]
        self.caminho_pai = self.pasta_dados / arquivo

        self.max_workers = 8
        self.max_pending = self.max_workers * 4
        self.checkpoints = CheckpointStore()

        self.stats = ContadorExecucao()
        self.required_output_keys = {
            "documento_fornecedor_normalizado",
            "tipo_documento_fornecedor",
            "cnpj_base_fornecedor",
            "orgao_origem",
            "endpoint_origem",
            "id_legislatura",
            "nome_deputado",
            "uri_deputado",
            "sigla_uf_deputado",
            "sigla_partido_deputado",
        }

    def _carregar_legislaturas(self):
        """Carrega o intervalo temporal de cada legislatura disponível."""

        caminho = self.pasta_dados / "legislaturas.json"
        legislaturas = {}

        if not caminho.exists():
            self.logger.warning("Arquivo de legislaturas nao encontrado: %s", caminho)
            return legislaturas

        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue

                try:
                    registro = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                data_inicio = registro.get("dataInicio")
                data_fim = registro.get("dataFim")
                if not data_inicio or not data_fim:
                    continue

                legislaturas[registro["id"]] = (
                    datetime.strptime(data_inicio, "%Y-%m-%d").date(),
                    datetime.strptime(data_fim, "%Y-%m-%d").date(),
                )

        return legislaturas

    def _anos_da_legislatura(
        self,
        id_legislatura: int,
        legislaturas: dict,
        periodo_inicio: date,
        periodo_fim: date,
    ):
        """Retorna apenas os anos em que legislatura e janela solicitada se cruzam."""

        intervalo = legislaturas.get(id_legislatura)
        if intervalo is None:
            return []

        inicio_leg, fim_leg = intervalo
        inicio = max(inicio_leg, periodo_inicio)
        fim = min(fim_leg, periodo_fim)

        if inicio > fim:
            return []

        return list(range(inicio.year, fim.year + 1))

    def _arquivo_saida(self, deputado, ano) -> Path:
        """Resolve o caminho final de saída do deputado no ano informado."""

        return (
            self.pasta_dados
            / "despesas_deputados_federais"
            / str(ano)
            / f"despesas_{deputado}.json"
        )

    def _stream_trabalhos(self, ano_inicio: int, ano_fim: int):
        """Gera tarefas válidas com contexto do deputado sem materializar a fila.

        O intervalo recebido segue a convenção do projeto: `ano_fim` é
        exclusivo. A geração prioriza arquivos de legislaturas mais recentes e
        anos mais novos para produzir resultados úteis mais cedo.
        """

        if not self.caminho_pai.exists():
            self.logger.warning("Caminho pai nao encontrado: %s", self.caminho_pai)
            return

        periodo_inicio = date(ano_inicio, 1, 1)
        periodo_fim = date(ano_fim - 1, 12, 31)
        legislaturas = self._carregar_legislaturas()
        vistos = set()

        if self.caminho_pai.is_dir():
            arquivos = sorted(
                self.caminho_pai.glob("*.json"),
                key=lambda path: int(path.stem.split("_")[-1]),
                reverse=True,
            )
        else:
            arquivos = [self.caminho_pai]

        for arquivo in arquivos:
            with open(arquivo, encoding="utf-8") as f:
                for linha in f:
                    try:
                        registro = json.loads(linha)
                    except json.JSONDecodeError:
                        continue

                    deputado = registro.get(self.campo_id)
                    id_legislatura = registro.get("id_legislatura") or registro.get("idLegislatura")

                    if deputado is None or id_legislatura is None:
                        continue

                    for ano in sorted(
                        self._anos_da_legislatura(
                            id_legislatura,
                            legislaturas,
                            periodo_inicio,
                            periodo_fim,
                        ),
                        reverse=True,
                    ):
                        chave = (str(deputado), ano)
                        if chave in vistos:
                            continue

                        vistos.add(chave)
                        yield deputado, ano, {
                            "id": deputado,
                            "id_legislatura": id_legislatura,
                            "nome": registro.get("nome"),
                            "siglaUf": registro.get("siglaUf"),
                            "siglaPartido": registro.get("siglaPartido"),
                            "uri": registro.get("uri"),
                        }

    def _incrementar(self, chave: str):
        """Atualiza estatísticas agregadas de execução de forma thread-safe."""

        self.stats.increment(chave)

    def _reutilizar_arquivo_legado(self, endpoint: str, deputado: str, contexto: str) -> bool:
        """Reaproveita arquivos já existentes e registra sucesso no checkpoint."""

        if self.checkpoints.get_status(endpoint, deputado, contexto) is not None:
            return False

        caminho = self._arquivo_saida(deputado, contexto)
        if not caminho.exists() or caminho.stat().st_size == 0:
            return False
        if not arquivo_jsonl_tem_chaves(caminho, self.required_output_keys):
            return False

        self.checkpoints.mark_success(
            endpoint=endpoint,
            entity_id=deputado,
            context=contexto,
            records=-1,
            pages=0,
            message="arquivo legado reutilizado",
        )
        self._incrementar("skipped")
        return True

    def _executar_tarefa(self, deputado, ano, contexto_deputado: dict | None = None):
        """Executa a extração de uma unidade de trabalho `(deputado, ano)`."""

        endpoint = self.nome_endpoint
        entity_id = str(deputado)
        contexto = str(ano)
        caminho_saida = self._arquivo_saida(entity_id, contexto)

        if self.checkpoints.is_terminal(endpoint, entity_id, contexto) and arquivo_jsonl_tem_chaves(
            caminho_saida,
            self.required_output_keys,
        ):
            self._incrementar("skipped")
            return

        if self._reutilizar_arquivo_legado(endpoint, entity_id, contexto):
            return

        self.checkpoints.mark_running(endpoint, entity_id, contexto)

        try:
            config = {
                **self.configuracao,
                "endpoint": self.endpoint_template.replace("{id}", entity_id),
                "params": {"ano": ano},
                "contexto_id": entity_id,
                "contexto_ano": ano,
                "contexto_deputado": contexto_deputado or {},
            }

            resumo = ExtratorDadosCamara(
                self.nome_endpoint,
                config,
                session=get_session(),
            ).executar()

            if resumo.get("status") == "skipped":
                self.checkpoints.mark_success(
                    endpoint=endpoint,
                    entity_id=entity_id,
                    context=contexto,
                    records=-1,
                    pages=0,
                    message="arquivo final reutilizado",
                )
                self._incrementar("skipped")
                return

            if resumo.get("status") == "skipped_empty":
                self.checkpoints.mark_empty(endpoint, entity_id, contexto, pages=0)
                self._incrementar("skipped")
                return

            if resumo["records"] == 0:
                self.checkpoints.mark_empty(endpoint, entity_id, contexto, pages=resumo["pages"])
                self._incrementar("empty")
                return

            self.checkpoints.mark_success(
                endpoint=endpoint,
                entity_id=entity_id,
                context=contexto,
                records=resumo["records"],
                pages=resumo["pages"],
            )
            self._incrementar("completed")

            self.logger.info(
                "Concluido | deputado=%s | ano=%s | paginas=%s | registros=%s",
                entity_id,
                ano,
                resumo["pages"],
                resumo["records"],
            )
        except Exception as exc:
            self.checkpoints.mark_error(endpoint, entity_id, contexto, str(exc))
            self._incrementar("failed")
            self.logger.exception("Falha | deputado=%s | ano=%s", entity_id, ano)

    def executar(self, ano_inicio=2000, ano_fim=2027):
        """Executa o crawler dependente para o intervalo de anos informado."""

        started_at = time.time()

        self.logger.info("Crawler iniciado | anos=%s-%s", ano_inicio, ano_fim)
        enviados = executar_tarefas_limitadas(
            self._stream_trabalhos(ano_inicio, ano_fim) or [],
            self._executar_tarefa,
            max_workers=self.max_workers,
            max_pending=self.max_pending,
        )

        if enviados == 0:
            self.logger.warning("Nenhum ID encontrado para alimentar %s", self.nome_endpoint)
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
