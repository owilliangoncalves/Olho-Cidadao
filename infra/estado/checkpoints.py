"""Persistência de checkpoints de execução baseada em arquivos JSON."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from pathlib import Path
from threading import Lock

from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import salvar_estado_json
from infra.estado.arquivos import slug_segmento


class CheckpointStore:
    """Armazena o estado de itens de trabalho em arquivos `.state.json`.

    O projeto usa exclusivamente artefatos de arquivo para persistir estados
    reaproveitáveis entre execuções.
    """

    def __init__(self, base_dir: str = "data/_estado/checkpoints"):
        """Inicializa o diretório de checkpoints."""

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _caminho_estado(self, endpoint: str, entity_id: str, context: str) -> Path:
        """Resolve o caminho do arquivo de estado de um item de trabalho."""

        return (
            self.base_dir
            / f"endpoint={slug_segmento(endpoint)}"
            / f"entity={slug_segmento(entity_id)}"
            / f"context={slug_segmento(context)}.state.json"
        )

    def _estado_inicial(self) -> dict:
        """Retorna a estrutura padrão de um checkpoint."""

        return {
            "endpoint": None,
            "entity_id": None,
            "context": None,
            "status": None,
            "attempts": 0,
            "records": 0,
            "pages": 0,
            "message": None,
            "updated_at": None,
        }

    def _agora_iso(self) -> str:
        """Retorna o horário atual em UTC no formato ISO-8601."""

        return datetime.now(timezone.utc).isoformat()

    def _carregar_estado(self, endpoint: str, entity_id: str, context: str) -> dict:
        """Carrega o estado atual do item a partir do arquivo correspondente."""

        caminho = self._caminho_estado(endpoint, entity_id, context)
        return carregar_estado_json(caminho, self._estado_inicial())

    def _salvar_estado(self, endpoint: str, entity_id: str, context: str, estado: dict):
        """Persiste o estado do item em um arquivo JSON dedicado."""

        caminho = self._caminho_estado(endpoint, entity_id, context)
        estado = {
            **self._estado_inicial(),
            **estado,
            "endpoint": endpoint,
            "entity_id": entity_id,
            "context": context,
        }
        salvar_estado_json(caminho, estado)

    def is_terminal(self, endpoint: str, entity_id: str, context: str) -> bool:
        """Indica se o item já chegou a um estado final reaproveitável."""

        status = self.get_status(endpoint, entity_id, context)
        return status in {"success", "empty"}

    def get_status(self, endpoint: str, entity_id: str, context: str) -> str | None:
        """Retorna o status atual do item, quando existir."""

        row = self._carregar_estado(endpoint, entity_id, context)
        return row.get("status")

    def mark_running(self, endpoint: str, entity_id: str, context: str):
        """Marca o item como em execução e incrementa o contador de tentativas."""

        with self._lock:
            estado = self._carregar_estado(endpoint, entity_id, context)
            estado["status"] = "running"
            estado["attempts"] = int(estado.get("attempts") or 0) + 1
            estado["message"] = None
            estado["updated_at"] = self._agora_iso()
            self._salvar_estado(endpoint, entity_id, context, estado)

    def mark_success(
        self,
        endpoint: str,
        entity_id: str,
        context: str,
        records: int,
        pages: int,
        message: str | None = None,
    ):
        """Marca a tarefa como concluída com metadados de volume."""

        with self._lock:
            estado = self._carregar_estado(endpoint, entity_id, context)
            estado["status"] = "success"
            estado["records"] = records
            estado["pages"] = pages
            estado["message"] = message
            estado["updated_at"] = self._agora_iso()
            self._salvar_estado(endpoint, entity_id, context, estado)

    def mark_empty(self, endpoint: str, entity_id: str, context: str, pages: int = 0):
        """Marca a tarefa como vazia, indicando que não houve dados retornados."""

        with self._lock:
            estado = self._carregar_estado(endpoint, entity_id, context)
            estado["status"] = "empty"
            estado["records"] = 0
            estado["pages"] = pages
            estado["message"] = None
            estado["updated_at"] = self._agora_iso()
            self._salvar_estado(endpoint, entity_id, context, estado)

    def mark_error(
        self,
        endpoint: str,
        entity_id: str,
        context: str,
        message: str,
    ):
        """Marca a tarefa como erro e persiste uma mensagem resumida."""

        with self._lock:
            estado = self._carregar_estado(endpoint, entity_id, context)
            estado["status"] = "error"
            estado["message"] = message[:1000]
            estado["updated_at"] = self._agora_iso()
            self._salvar_estado(endpoint, entity_id, context, estado)
