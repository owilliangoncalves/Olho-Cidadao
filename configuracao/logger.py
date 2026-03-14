"""Configuração central de logging do projeto."""

from __future__ import annotations

import logging
import os
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "log.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def _resolver_nivel() -> int:
    """Resolve o nível de log a partir da variável `LOG_LEVEL`."""

    nivel = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, nivel, logging.INFO)


def configurar_logging() -> logging.Logger:
    """Configura o logger raiz de forma idempotente.

    O projeto usa múltiplos loggers nomeados. Por isso, a configuração é feita
    no logger raiz uma única vez, com saída em arquivo e no console.
    """

    LOG_DIR.mkdir(exist_ok=True)
    root = logging.getLogger()

    if getattr(configurar_logging, "_configured", False):
        root.setLevel(_resolver_nivel())
        return logging.getLogger("br_etl")

    root.setLevel(_resolver_nivel())

    formatter = logging.Formatter(LOG_FORMAT)
    possui_file_handler = any(
        isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == LOG_FILE
        for handler in root.handlers
    )
    possui_stream_handler = any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        for handler in root.handlers
    )

    if not possui_file_handler:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    if not possui_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    configurar_logging._configured = True
    return logging.getLogger("br_etl")


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger nomeado após garantir a configuração global."""

    configurar_logging()
    return logging.getLogger(name)


logger = get_logger("br_etl")
