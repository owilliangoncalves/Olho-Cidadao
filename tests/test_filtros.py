"""Testes para normalização de filtros e slugs de consulta."""

import unittest

from utils.filtros import parse_filtros_cli
from utils.filtros import slug_filtros


class FiltrosTestCase(unittest.TestCase):
    """Exercita os helpers usados por várias integrações."""

    def test_parse_filtros_cli_converte_tipos_simples(self):
        """A CLI deve coerir inteiros, booleanos e floats quando possível."""

        filtros = parse_filtros_cli(
            ["exercicio=2025", "ativo=true", "valor=10.5", "texto=abc"]
        )
        self.assertEqual(
            filtros,
            {
                "exercicio": 2025,
                "ativo": True,
                "valor": 10.5,
                "texto": "abc",
            },
        )

    def test_parse_filtros_cli_rejeita_formato_invalido(self):
        """Itens fora do padrão `chave=valor` devem falhar cedo."""

        with self.assertRaises(ValueError):
            parse_filtros_cli(["sem-separador"])

    def test_slug_filtros_sem_filtros(self):
        """Sem filtros, o slug padrão deve ser `all`."""

        self.assertEqual(slug_filtros(None), "all")
        self.assertEqual(slug_filtros({}), "all")

    def test_slug_filtros_gera_saida_estavel(self):
        """A ordem dos filtros não deve alterar a assinatura final."""

        slug_a = slug_filtros({"b": 2, "a": 1})
        slug_b = slug_filtros({"a": 1, "b": 2})
        self.assertEqual(slug_a, slug_b)


if __name__ == "__main__":
    unittest.main()
