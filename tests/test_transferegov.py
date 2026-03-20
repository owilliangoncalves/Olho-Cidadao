"""Testes do pacote Transferegov."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from extracao.transferegov import RESOURCE_GROUPS
from extracao.transferegov import TransferegovConfig
from extracao.transferegov import TransferegovRecursos
from extracao.transferegov.tarefas import output_path_recurso
from extracao.transferegov.tarefas import resolver_recursos_grupo
from infra.errors import UserInputError


class TransferegovHelpersTestCase(unittest.TestCase):
    """Valida helpers puros usados pelo pacote."""

    def test_resolver_recursos_grupo_separa_validos_e_invalidos(self):
        """Recursos inválidos não devem contaminar a fila válida."""

        validos, invalidos = resolver_recursos_grupo(
            "especial",
            ["programa_especial", "foo", "programa_especial", "bar"],
        )

        self.assertEqual(validos, ("programa_especial",))
        self.assertEqual(invalidos, ("foo", "bar"))

    def test_output_path_recurso_monta_saida_padrao(self):
        """O caminho relativo deve refletir grupo, recurso e assinatura."""

        self.assertEqual(
            output_path_recurso("ted", "trf", {"ano": 2024, "uf": "sp"}).as_posix(),
            "transferegov/ted/trf/consulta=ano=2024__uf=sp.json",
        )


class TransferegovConfigTestCase(unittest.TestCase):
    """Valida o contrato de configuração do pacote."""

    def test_carregar_aplica_override_local_de_page_size(self):
        """O page size explícito deve prevalecer sobre o config do projeto."""

        with patch(
            "extracao.transferegov.config.obter_parametros_extrator",
            return_value={
                "page_size": 1000,
                "rate_limit_per_sec": 1.5,
                "max_rate_per_sec": 3.0,
            },
        ):
            cfg = TransferegovConfig.carregar(grupo="especial", page_size=77)

        self.assertEqual(cfg.grupo, "especial")
        self.assertEqual(cfg.page_size, 77)
        self.assertEqual(cfg.rate_limit_per_sec, 1.5)

    def test_rejeita_grupo_desconhecido(self):
        """Grupos fora do catálogo devem falhar cedo."""

        with self.assertRaises(UserInputError):
            TransferegovConfig.carregar(grupo="foo", page_size=None)


class TransferegovRecursosTestCase(unittest.TestCase):
    """Valida a fachada pública e a orquestração do pacote."""

    def test_reexporta_catalogo_publico(self):
        """O catálogo público deve permanecer acessível pela API do pacote."""

        self.assertIn("especial", RESOURCE_GROUPS)
        self.assertIn("programa_especial", RESOURCE_GROUPS["especial"])

    def test_fachada_publica_exporta_orquestrador_do_pacote(self):
        """A classe pública deve se apresentar como parte de `extracao.transferegov`."""

        self.assertEqual(TransferegovRecursos.__module__, "extracao.transferegov")

    def test_executar_ignora_invalidos_e_processa_validos(self):
        """O orquestrador deve seguir com os recursos válidos restantes."""

        extrator = TransferegovRecursos("especial", page_size=77)

        with patch.object(
            extrator,
            "_executar_tarefa_paginada",
            return_value={"status": "success", "records": 12, "pages": 1},
        ) as executar:
            resultados = extrator.executar(
                ["programa_especial", "foo", "programa_especial"],
                filtros={"uf": "sp"},
            )

        self.assertEqual(tuple(resultados), ("programa_especial",))
        kwargs = executar.call_args.kwargs
        self.assertEqual(kwargs["endpoint"], "/programa_especial")
        self.assertEqual(kwargs["base_params"], {"uf": "sp"})
        self.assertEqual(kwargs["context"]["grupo_api"], "especial")
        self.assertEqual(
            kwargs["relative_output_path"].as_posix(),
            "transferegov/especial/programa_especial/consulta=uf=sp.json",
        )
        self.assertEqual(kwargs["pagination"]["style"], "offset")
        self.assertEqual(kwargs["pagination"]["page_size"], 77)

    def test_executar_retorna_vazio_quando_nao_ha_recurso_valido(self):
        """Quando tudo é inválido, o pacote deve encerrar sem chamadas HTTP."""

        extrator = TransferegovRecursos("ted")

        with patch.object(extrator, "_executar_tarefa_paginada") as executar:
            resultados = extrator.executar(["foo"])

        self.assertEqual(resultados, {})
        executar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
