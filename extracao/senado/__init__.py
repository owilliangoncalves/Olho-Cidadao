"""Pacote Senado com fachada publica e orquestracao concentradas aqui."""

from __future__ import annotations

from extracao.extrator_da_base import ExtratorBase
from extracao.senado.arquivos import artefatos_ano_senado
from extracao.senado.arquivos import estado_inicial_senado
from extracao.senado.config import SenadoConfig
from extracao.senado.dados import iterar_despesas_senado
from extracao.senado.persistencia import salvar_despesas_ano
from extracao.senado.tarefas import contador_por_status
from extracao.senado.tarefas import iterar_anos_senado
from infra.concorrencia import ContadorExecucao
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json


class DadosSenado(ExtratorBase):
    """Extrai o endpoint de despesas do Senado e salva por ano."""

    def __init__(self, nome_endpoint: str):
        """Configura o endpoint e o intervalo de anos a processar."""

        super().__init__(orgao="senado")
        self.cfg = SenadoConfig.carregar(nome_endpoint)
        self.stats = ContadorExecucao()

    def _executar_ano(
        self,
        ano: int,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ) -> str:
        """Executa um exercicio do CEAPS com uma retentativa de `.empty`."""

        arquivos = artefatos_ano_senado(ano)
        if arquivos.pronto():
            self.logger.info("[%s] Ano %s ja existe, pulando.", self.orgao, ano)
            return "skipped"

        retrying_from_empty = _from_empty_retry
        if arquivos.empty.exists():
            if _allow_empty_retry and self._consumir_retry_empty(
                arquivos.empty,
                contexto=f"senado:ceaps:{ano}",
            ):
                retrying_from_empty = True
            else:
                self.logger.info("[%s] Ano %s ja foi marcado como vazio, pulando.", self.orgao, ano)
                return "skipped_empty"

        estado = carregar_estado_json(arquivos.estado, estado_inicial_senado())
        estado_execucao = {
            **estado,
            "status": "running",
            "attempts": int(estado.get("attempts") or 0) + 1,
        }
        salvar_estado_json(arquivos.estado, estado_execucao)

        try:
            self.logger.info("[%s] Processando ano: %s", self.orgao, ano)
            resposta = self._fazer_requisicao(self.cfg.endpoint.format(ano=ano), delay=0)
            total = salvar_despesas_ano(
                arquivos,
                iterar_despesas_senado(resposta),
                ano=ano,
                nome_endpoint=self.cfg.nome_endpoint,
                logger=self.logger,
                orgao=self.orgao,
            )

            if total == 0:
                limpar_artefatos(arquivos.estado, arquivos.temporario)
                if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                    arquivos.empty,
                    contexto=f"senado:ceaps:{ano}",
                ):
                    return self._executar_ano(
                        ano,
                        _allow_empty_retry=False,
                        _from_empty_retry=True,
                    )

                if not _from_empty_retry:
                    arquivos.empty.touch()
                elif arquivos.empty.exists():
                    arquivos.empty.unlink()
                salvar_estado_json(
                    arquivos.estado,
                    {
                        **estado_execucao,
                        "status": "empty",
                        "records": 0,
                    },
                )
                self.logger.warning("[%s] Nenhum registro encontrado para o ano %s", self.orgao, ano)
                return "empty"

            if arquivos.empty.exists():
                arquivos.empty.unlink()

            limpar_artefatos(arquivos.estado)
            self.logger.info("[%s] Ano %s concluido com %s registros.", self.orgao, ano, total)
            return "success"
        except Exception as exc:
            salvar_estado_json(
                arquivos.estado,
                {
                    **estado_execucao,
                    "status": "error",
                    "message": str(exc)[:1000],
                },
            )
            self.logger.exception("[%s] Falha critica no ano %s", self.orgao, ano)
            return "error"

    def executar(self):
        """Percorre os anos configurados e processa o CEAPS de cada exercicio."""

        self.logger.info(
            "[%s] Iniciando processamento de %s ate %s",
            self.orgao,
            self.cfg.ano_inicio,
            self.cfg.ano_fim,
        )

        for ano in iterar_anos_senado(self.cfg.ano_inicio, self.cfg.ano_fim):
            self.stats.increment(contador_por_status(self._executar_ano(ano)))

        stats = self.stats.snapshot()
        self.logger.info(
            "[%s] Extracao concluida | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            self.orgao,
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )


__all__ = ["DadosSenado", "SenadoConfig"]
