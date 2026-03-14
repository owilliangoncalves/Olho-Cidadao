"""Testes para a configuração compartilhada de logging."""

from __future__ import annotations

import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import configuracao.logger as logger_module


class LoggerConfigTestCase(unittest.TestCase):
    """Garante que a configuração de logging seja idempotente."""

    def test_configurar_logging_nao_duplica_handlers(self):
        """Chamadas repetidas não devem multiplicar handlers globais."""

        with TemporaryDirectory() as tmp:
            root = logging.getLogger()
            handlers_originais = list(root.handlers)
            configured_original = getattr(logger_module.configurar_logging, "_configured", False)

            try:
                root.handlers = []
                if hasattr(logger_module.configurar_logging, "_configured"):
                    delattr(logger_module.configurar_logging, "_configured")

                with mock.patch.object(logger_module, "LOG_DIR", Path(tmp)):
                    with mock.patch.object(logger_module, "LOG_FILE", Path(tmp) / "log.log"):
                        primeiro = logger_module.configurar_logging()
                        handlers_primeira_chamada = len(root.handlers)
                        segundo = logger_module.configurar_logging()

                self.assertEqual(handlers_primeira_chamada, len(root.handlers))
                self.assertEqual(primeiro.name, "br_etl")
                self.assertEqual(segundo.name, "br_etl")
            finally:
                for handler in root.handlers:
                    try:
                        handler.close()
                    except Exception:
                        continue
                root.handlers = handlers_originais
                if configured_original:
                    logger_module.configurar_logging._configured = configured_original
                elif hasattr(logger_module.configurar_logging, "_configured"):
                    delattr(logger_module.configurar_logging, "_configured")


if __name__ == "__main__":
    unittest.main()
