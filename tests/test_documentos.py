"""Testes para utilitários de documentos."""

import unittest

from utils.documentos import base_cnpj
from utils.documentos import normalizar_documento
from utils.documentos import tipo_documento


class DocumentosTestCase(unittest.TestCase):
    """Valida a normalização de CPF e CNPJ."""

    def test_normalizar_documento_retorna_apenas_digitos(self):
        """Documentos válidos devem ser devolvidos sem máscara."""

        self.assertEqual(normalizar_documento("12.345.678/0001-90"), "12345678000190")
        self.assertEqual(normalizar_documento("123.456.789-09"), "12345678909")

    def test_normalizar_documento_rejeita_tamanho_invalido(self):
        """Valores incompatíveis com CPF ou CNPJ retornam `None`."""

        self.assertIsNone(normalizar_documento("123"))
        self.assertIsNone(normalizar_documento(None))

    def test_tipo_e_base_cnpj(self):
        """A tipagem e a raiz do CNPJ devem ser derivadas corretamente."""

        self.assertEqual(tipo_documento("12345678000190"), "cnpj")
        self.assertEqual(tipo_documento("12345678909"), "cpf")
        self.assertIsNone(tipo_documento(None))
        self.assertEqual(base_cnpj("12345678000190"), "12345678")
        self.assertIsNone(base_cnpj("12345678909"))


if __name__ == "__main__":
    unittest.main()
