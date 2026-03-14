"""Extratores da API pública do ObrasGov."""

from __future__ import annotations

import json
import re
from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.publica.base import ExtratorAPIPublicaBase
from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas
from utils.filtros import slug_filtros

PAGEABLE_RESOURCES = {
    "projeto-investimento": "/projeto-investimento",
    "execucao-fisica": "/execucao-fisica",
    "execucao-financeira": "/execucao-financeira",
}


def _slug_id(valor: str) -> str:
    """Normaliza um identificador para uso em nome de arquivo."""

    return re.sub(r"[^0-9A-Za-z._-]+", "-", valor).strip("-") or "desconhecido"


class ExtratorObrasGov(ExtratorAPIPublicaBase):
    """Extrai projetos, execuções e geometrias do ObrasGov."""

    def __init__(self, page_size: int | None = None):
        """Configura limites de tráfego e concorrência do crawler."""

        config = obter_parametros_extrator("obrasgov")
        super().__init__(
            orgao="obrasgov",
            nome_endpoint="obras_publicas",
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
        self.page_size = page_size if page_size is not None else config.get("page_size")
        self.max_workers = config.get("max_workers")
        self.max_pending = self.max_workers * 4
        self.stats = ContadorExecucao()

    def executar(self, recursos: list[str] | None = None, filtros: dict | None = None):
        """Mantém compatibilidade com a base abstrata executando os recursos paginados."""

        self.executar_recursos(recursos=recursos, filtros=filtros)

    def _incrementar(self, chave: str):
        """Atualiza estatísticas de execução de forma thread-safe."""

        self.stats.increment(chave)

    def executar_recursos(self, recursos: list[str] | None = None, filtros: dict | None = None):
        """Extrai recursos paginados do ObrasGov."""

        assinatura = slug_filtros(filtros)
        recursos_selecionados = recursos or list(PAGEABLE_RESOURCES)

        for recurso in recursos_selecionados:
            endpoint = PAGEABLE_RESOURCES[recurso]
            resumo = self._executar_tarefa_paginada(
                endpoint=endpoint,
                base_params=filtros or {},
                relative_output_path=(
                    Path("obrasgov") / recurso / f"consulta={assinatura}.json"
                ),
                context={
                    "dataset": recurso,
                    "filtros": filtros or {},
                },
                pagination={
                    "style": "page",
                    "page_param": "pagina",
                    "page_size_param": "tamanhoDaPagina",
                    "page_size": self.page_size,
                    "start_page": 1,
                },
            )

            self.logger.info(
                "[OBRASGOV] Recurso concluido | recurso=%s | status=%s | registros=%s",
                recurso,
                resumo["status"],
                resumo["records"],
            )

    def _iterar_arquivos_projetos(self):
        """Lista arquivos de projetos, incluindo temporários sem final correspondente."""

        caminho = Path("data/obrasgov/projeto-investimento")
        if not caminho.exists():
            return []

        arquivos_finais = sorted(caminho.glob("**/*.json"))
        arquivos_temporarios = sorted(
            arquivo
            for arquivo in caminho.glob("**/*.json.tmp")
            if not arquivo.with_suffix("").exists()
        )
        return [*arquivos_finais, *arquivos_temporarios]

    def _iterar_ids_projetos(self):
        """Lê `idUnico` dos projetos finalizados ou já persistidos em `.tmp`."""

        arquivos = self._iterar_arquivos_projetos()
        if not arquivos:
            return

        vistos = set()
        for arquivo in arquivos:
            with open(arquivo, encoding="utf-8") as f:
                for linha in f:
                    if not linha.strip():
                        continue
                    try:
                        registro = json.loads(linha)
                    except json.JSONDecodeError:
                        continue

                    payload = registro.get("payload", {})
                    id_unico = payload.get("idUnico")
                    if not id_unico or id_unico in vistos:
                        continue

                    vistos.add(id_unico)
                    yield id_unico

    def _executar_geometria(self, id_unico: str):
        """Executa a extração da geometria de um projeto específico."""

        try:
            resumo = self._executar_tarefa_unica(
                endpoint="/geometria",
                params={"idUnico": id_unico},
                relative_output_path=(
                    Path("obrasgov")
                    / "geometria"
                    / f"projeto={_slug_id(id_unico)}.json"
                ),
                context={
                    "dataset": "geometria",
                    "id_unico": id_unico,
                },
                wrap_dict=True,
            )

            if resumo["status"] == "success":
                self._incrementar("completed")
            elif resumo["status"] == "skipped":
                self._incrementar("skipped")
            else:
                self._incrementar("empty")
        except Exception:
            self._incrementar("failed")
            self.logger.exception("[OBRASGOV] Falha em geometria | id_unico=%s", id_unico)

    def executar_geometrias(self, limit_ids: int | None = None):
        """Extrai geometrias para os projetos já persistidos localmente."""

        ids = self._iterar_ids_projetos() or []
        if limit_ids is not None:
            ids = (
                id_unico
                for indice, id_unico in enumerate(ids)
                if indice < limit_ids
            )

        executar_tarefas_limitadas(
            ids,
            self._executar_geometria,
            max_workers=self.max_workers,
            max_pending=self.max_pending,
        )
        stats = self.stats.snapshot()

        self.logger.info(
            "[OBRASGOV] Geometrias finalizadas | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
