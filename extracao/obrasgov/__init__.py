"""Pacote ObrasGov com fachada pública e orquestração concentradas aqui."""

from __future__ import annotations

from functools import cache
from typing import Any

from extracao.obrasgov.config import OBRASGOV_PAGINACAO
from extracao.obrasgov.config import ObrasGovConfig
from extracao.obrasgov.config import PAGEABLE_RESOURCES
from extracao.obrasgov.projetos import iterar_ids_projetos
from extracao.obrasgov.projetos import slug_id
from extracao.obrasgov.tarefas import contador_por_status
from extracao.obrasgov.tarefas import output_path_geometria
from extracao.obrasgov.tarefas import output_path_recurso
from extracao.obrasgov.tarefas import resolver_recursos_paginados
from utils.filtros import slug_filtros


def executar_tarefas_limitadas(*args, **kwargs):
    """Importa o executor concorrente apenas quando necessário."""

    from infra.concorrencia import executar_tarefas_limitadas as executar

    return executar(*args, **kwargs)


@cache
def _construir_obrasgov():
    """Cria e memoriza o orquestrador público do pacote."""

    from extracao.publica import ExtratorAPIPublicaBase
    from infra.concorrencia import ContadorExecucao

    class ObrasGov(ExtratorAPIPublicaBase):
        """Extrai projetos, execuções e geometrias do ObrasGov."""

        def __init__(self, page_size: int | None = None):
            self.cfg = ObrasGovConfig.carregar(page_size=page_size)
            super().__init__(
                orgao="obrasgov",
                nome_endpoint="obras_publicas",
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )
            self.stats = ContadorExecucao()

        def executar(self, recursos: list[str] | None = None, filtros: dict | None = None):
            """Implementa a interface da base delegando para recursos paginados."""

            return self.executar_recursos(recursos=recursos, filtros=filtros)

        def executar_recursos(
            self,
            recursos: list[str] | None = None,
            filtros: dict | None = None,
        ):
            """Extrai recursos paginados do ObrasGov."""

            recursos_validos, recursos_invalidos = resolver_recursos_paginados(recursos)
            for recurso in recursos_invalidos:
                self.logger.warning("[OBRASGOV] Recurso desconhecido, pulando | recurso=%s", recurso)

            if not recursos_validos:
                self.logger.warning("[OBRASGOV] Nenhum recurso válido informado.")
                return {}

            assinatura = slug_filtros(filtros)
            resultados: dict[str, dict] = {}
            for recurso in recursos_validos:
                resumo = self._executar_tarefa_paginada(
                    endpoint=PAGEABLE_RESOURCES[recurso],
                    base_params=filtros or {},
                    relative_output_path=output_path_recurso(recurso, assinatura),
                    context={"dataset": recurso, "filtros": filtros or {}},
                    pagination={**OBRASGOV_PAGINACAO, "page_size": self.cfg.page_size},
                )
                resultados[recurso] = resumo
                self.logger.info(
                    "[OBRASGOV] Recurso concluido | recurso=%s | status=%s | registros=%s",
                    recurso,
                    resumo["status"],
                    resumo["records"],
                )

            return resultados

        def _executar_geometria(self, id_unico: str):
            """Executa a extração da geometria de um projeto específico."""

            try:
                resumo = self._executar_tarefa_unica(
                    endpoint="/geometria",
                    params={"idUnico": id_unico},
                    relative_output_path=output_path_geometria(id_unico),
                    context={"dataset": "geometria", "id_unico": id_unico},
                    wrap_dict=True,
                )
                self.stats.increment(contador_por_status(resumo.get("status")))
            except Exception:
                self.stats.increment("failed")
                self.logger.exception("[OBRASGOV] Falha em geometria | id_unico=%s", id_unico)

        def executar_geometrias(self, limit_ids: int | None = None):
            """Extrai geometrias para os projetos já persistidos localmente."""

            ids = iterar_ids_projetos() or ()
            if limit_ids is not None:
                ids = (
                    id_unico
                    for indice, id_unico in enumerate(ids)
                    if indice < limit_ids
                )

            enviados = executar_tarefas_limitadas(
                ids,
                self._executar_geometria,
                max_workers=self.cfg.max_workers,
                max_pending=self.cfg.max_pending,
            )
            if enviados == 0:
                self.logger.warning("[OBRASGOV] Nenhum projeto encontrado para extrair geometria.")
                return

            stats = self.stats.snapshot()
            self.logger.info(
                "[OBRASGOV] Geometrias finalizadas | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
                stats["completed"],
                stats["skipped"],
                stats["empty"],
                stats["failed"],
            )

    ObrasGov.__module__ = __name__
    return ObrasGov


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "ObrasGov":
        obrasgov = _construir_obrasgov()
        globals()[name] = obrasgov
        return obrasgov
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantém introspecção consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "OBRASGOV_PAGINACAO",
    "ObrasGov",
    "ObrasGovConfig",
    "PAGEABLE_RESOURCES",
    "iterar_ids_projetos",
    "slug_id",
]
