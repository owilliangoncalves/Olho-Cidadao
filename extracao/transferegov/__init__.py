"""Pacote Transferegov com fachada pública e orquestração concentradas aqui."""

from __future__ import annotations

from functools import cache
from typing import Any

from extracao.transferegov.config import ORGAO_MAP
from extracao.transferegov.config import RESOURCE_GROUPS
from extracao.transferegov.config import TRANSFEREGOV_PAGINACAO
from extracao.transferegov.config import TransferegovConfig
from extracao.transferegov.config import validar_grupo_transferegov
from extracao.transferegov.tarefas import output_path_recurso
from extracao.transferegov.tarefas import resolver_recursos_grupo


@cache
def _construir_transferegov():
    """Cria e memoriza o orquestrador público do pacote."""

    from extracao.publica import ExtratorAPIPublicaBase

    class TransferegovRecursos(ExtratorAPIPublicaBase):
        """Extrai datasets paginados das APIs do ecossistema Transferegov."""

        def __init__(self, grupo: str, page_size: int | None = None):
            self.cfg = TransferegovConfig.carregar(grupo=grupo, page_size=page_size)
            super().__init__(
                orgao=ORGAO_MAP[self.cfg.grupo],
                nome_endpoint=self.cfg.grupo,
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )
            self.grupo = self.cfg.grupo

        def executar(
            self,
            recursos: list[str] | None = None,
            filtros: dict | None = None,
        ):
            """Extrai os recursos válidos do grupo configurado."""

            recursos_validos, recursos_invalidos = resolver_recursos_grupo(
                self.grupo,
                recursos,
            )
            for recurso in recursos_invalidos:
                self.logger.warning(
                    "[TRANSFEREGOV] Recurso desconhecido, pulando | grupo=%s | recurso=%s",
                    self.grupo,
                    recurso,
                )

            if not recursos_validos:
                self.logger.warning(
                    "[TRANSFEREGOV] Nenhum recurso válido informado | grupo=%s",
                    self.grupo,
                )
                return {}

            resultados: dict[str, dict] = {}
            for recurso in recursos_validos:
                resumo = self._executar_tarefa_paginada(
                    endpoint=f"/{recurso}",
                    base_params=filtros or {},
                    relative_output_path=output_path_recurso(self.grupo, recurso, filtros),
                    context={
                        "dataset": recurso,
                        "grupo_api": self.grupo,
                        "filtros": filtros or {},
                    },
                    pagination={
                        **TRANSFEREGOV_PAGINACAO,
                        "page_size": self.cfg.page_size,
                    },
                )
                resultados[recurso] = resumo
                self.logger.info(
                    "[TRANSFEREGOV] Recurso concluido | grupo=%s | recurso=%s | status=%s | registros=%s",
                    self.grupo,
                    recurso,
                    resumo["status"],
                    resumo["records"],
                )

            return resultados

    TransferegovRecursos.__module__ = __name__
    return TransferegovRecursos


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "TransferegovRecursos":
        recursos = _construir_transferegov()
        globals()[name] = recursos
        return recursos
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantém introspecção consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "ORGAO_MAP",
    "RESOURCE_GROUPS",
    "TRANSFEREGOV_PAGINACAO",
    "TransferegovConfig",
    "TransferegovRecursos",
    "output_path_recurso",
    "resolver_recursos_grupo",
    "validar_grupo_transferegov",
]
