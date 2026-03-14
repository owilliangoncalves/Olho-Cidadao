"""Testes para a estratégia padronizada de checkpoints."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from infra.estado.checkpoints import CheckpointStore


class CheckpointStoreTestCase(unittest.TestCase):
    """Garante o ciclo básico de vida dos checkpoints em arquivo."""

    def test_checkpoint_store_persiste_estados_em_json(self):
        """A marcação de estados deve sobreviver à releitura do store."""

        with TemporaryDirectory() as tmp:
            base_dir = Path(tmp) / "checkpoints"
            store = CheckpointStore(
                base_dir=str(base_dir),
                legacy_sqlite_path=str(Path(tmp) / "legacy.sqlite3"),
            )

            store.mark_running("demo", "123", "2025")
            store.mark_success("demo", "123", "2025", records=10, pages=2)

            self.assertEqual(store.get_status("demo", "123", "2025"), "success")
            self.assertTrue(store.is_terminal("demo", "123", "2025"))

            arquivos = sorted(base_dir.rglob("*.json"))
            self.assertEqual(len(arquivos), 1)
            self.assertIn("context=2025.state.json", str(arquivos[0]))

    def test_checkpoint_store_marca_vazio_e_erro(self):
        """Estados finais diferentes devem ser refletidos corretamente."""

        with TemporaryDirectory() as tmp:
            store = CheckpointStore(
                base_dir=f"{tmp}/checkpoints",
                legacy_sqlite_path=f"{tmp}/legacy.sqlite3",
            )

            store.mark_empty("demo", "999", "2024", pages=0)
            self.assertEqual(store.get_status("demo", "999", "2024"), "empty")
            self.assertTrue(store.is_terminal("demo", "999", "2024"))

            store.mark_error("demo", "999", "2024", "falha")
            self.assertEqual(store.get_status("demo", "999", "2024"), "error")
            self.assertFalse(store.is_terminal("demo", "999", "2024"))


if __name__ == "__main__":
    unittest.main()
