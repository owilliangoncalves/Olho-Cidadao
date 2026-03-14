"""Testes para os helpers compartilhados de concorrência."""

from __future__ import annotations

import unittest

from infra.concorrencia import ContadorExecucao
from infra.concorrencia import executar_tarefas_limitadas


class ConcorrenciaTestCase(unittest.TestCase):
    """Valida o comportamento básico dos utilitários de paralelismo."""

    def test_contador_execucao_incrementa_com_snapshot_estavel(self):
        """Os contadores devem refletir os incrementos aplicados."""

        contador = ContadorExecucao()
        contador.increment("completed")
        contador.increment("failed")
        contador.increment("failed")

        self.assertEqual(
            contador.snapshot(),
            {
                "completed": 1,
                "skipped": 0,
                "empty": 0,
                "failed": 2,
            },
        )

    def test_executar_tarefas_limitadas_processa_tuplas_e_retorna_quantidade(self):
        """O executor deve expandir tuplas em args e contar tarefas enviadas."""

        resultados = []

        def worker(valor: int, fator: int):
            resultados.append(valor * fator)

        enviados = executar_tarefas_limitadas(
            [(1, 10), (2, 10), (3, 10)],
            worker,
            max_workers=2,
            max_pending=2,
        )

        self.assertEqual(enviados, 3)
        self.assertEqual(sorted(resultados), [10, 20, 30])


if __name__ == "__main__":
    unittest.main()
