"""Pacote Siconfi com fachada publica e orquestracao concentradas aqui."""

from __future__ import annotations

from functools import cache
from typing import Any

from extracao.siconfi.config import SICONFI_PAGINACAO
from extracao.siconfi.config import SiconfiConfig
from extracao.siconfi.specs import SICONFI_RESOURCES
from extracao.siconfi.tarefas import preparar_consultas_siconfi
from extracao.siconfi.tarefas import output_path_recurso


@cache
def _construir_siconfi():
    """Cria e memoriza o orquestrador publico do pacote."""

    from extracao.publica import ExtratorAPIPublicaBase

    class Siconfi(ExtratorAPIPublicaBase):
        """Extrai datasets paginados da plataforma Siconfi."""

        def __init__(self, page_size: int | None = None):
            self.cfg = SiconfiConfig.carregar(page_size=page_size)
            super().__init__(
                orgao="siconfi",
                nome_endpoint="dados_abertos",
                rate_limit_per_sec=self.cfg.rate_limit_per_sec,
                max_rate_per_sec=self.cfg.max_rate_per_sec,
            )
            self.required_meta_keys = {
                *self.required_meta_keys,
                "dataset",
                "filtros",
            }

        def executar(self, recursos: list[str] | None = None, filtros: dict | None = None):
            """Extrai os recursos desejados do Siconfi."""

            resultados: dict[str, dict] = {}
            for recurso, spec, filtros_recurso in preparar_consultas_siconfi(recursos, filtros):
                resumo = self._executar_tarefa_paginada(
                    endpoint=spec.path,
                    base_params=filtros_recurso,
                    relative_output_path=output_path_recurso(recurso, filtros_recurso),
                    context={
                        "dataset": recurso,
                        "filtros": filtros_recurso,
                    },
                    pagination={**SICONFI_PAGINACAO, "page_size": self.cfg.page_size},
                    item_keys=("items", "data"),
                )
                resultados[recurso] = resumo
                self.logger.info(
                    "[SICONFI] Recurso concluido | recurso=%s | status=%s | registros=%s",
                    recurso,
                    resumo["status"],
                    resumo["records"],
                )

            return resultados

    Siconfi.__module__ = __name__
    return Siconfi


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "Siconfi":
        siconfi = _construir_siconfi()
        globals()[name] = siconfi
        return siconfi
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantem introspeccao consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = [
    "SICONFI_PAGINACAO",
    "SICONFI_RESOURCES",
    "Siconfi",
    "SiconfiConfig",
    "preparar_consultas_siconfi",
]
