"""Helpers compartilhados para concorrência limitada em crawlers."""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Lock
from typing import Iterable


class ContadorExecucao:
    """Mantém contadores de execução de forma thread-safe."""

    DEFAULT_KEYS = ("completed", "skipped", "empty", "failed")

    def __init__(self, *keys: str):
        """Inicializa os contadores informados ou o conjunto padrão."""

        self._stats = {chave: 0 for chave in (keys or self.DEFAULT_KEYS)}
        self._lock = Lock()

    def increment(self, chave: str):
        """Incrementa um contador existente."""

        with self._lock:
            self._stats[chave] = int(self._stats.get(chave, 0)) + 1

    def snapshot(self) -> dict[str, int]:
        """Retorna uma cópia estável do estado atual dos contadores."""

        with self._lock:
            return dict(self._stats)


def executar_tarefas_limitadas(
    tarefas: Iterable,
    worker,
    *,
    max_workers: int,
    max_pending: int | None = None,
) -> int:
    """Executa tarefas com paralelismo limitado e backpressure local.

    Args:
        tarefas: Iterável de itens. Tuplas e listas são expandidas como
            argumentos posicionais do `worker`.
        worker: Função executada por item.
        max_workers: Quantidade máxima de workers simultâneos.
        max_pending: Quantidade máxima de futures pendentes antes de bloquear.

    Returns:
        Número de tarefas enviadas ao executor.
    """

    max_workers = max(1, int(max_workers))
    max_pending = max_pending or (max_workers * 4)
    enviados = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = set()

        for tarefa in tarefas or []:
            enviados += 1
            args = tarefa if isinstance(tarefa, (tuple, list)) else (tarefa,)
            futures.add(executor.submit(worker, *args))

            if len(futures) >= max_pending:
                done, futures = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    future.result()

        for future in futures:
            future.result()

    return enviados
