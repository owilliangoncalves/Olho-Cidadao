"""Testes para a consolidação CSV da Câmara."""

import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.gera_csv import ConversorDespesasCSV


class ConversorDespesasCSVTestCase(unittest.TestCase):
    """Valida a geração do CSV consolidado a partir de JSON Lines locais."""

    def test_consolidador_gera_csv_com_colunas_esperadas(self):
        """Uma despesa válida deve resultar em um CSV com cabeçalho e uma linha."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            despesas_dir = base / "data" / "despesas_deputados_federais" / "2025"
            despesas_dir.mkdir(parents=True)

            registro = {
                "id_deputado": "123",
                "id_legislatura": 57,
                "nome_deputado": "Deputado Exemplo",
                "uri_deputado": "https://dadosabertos.camara.leg.br/api/v2/deputados/123",
                "sigla_uf_deputado": "SP",
                "sigla_partido_deputado": "ABC",
                "nomeFornecedor": "Fornecedor Exemplo",
                "cnpjCpfFornecedor": "12345678000190",
                "documento_fornecedor_normalizado": "12345678000190",
                "tipo_documento_fornecedor": "cnpj",
                "cnpj_base_fornecedor": "12345678",
                "valorLiquido": "100.00",
                "ano": 2025,
                "mes": 3,
                "tipoDespesa": "COMBUSTÍVEIS E LUBRIFICANTES.",
            }

            arquivo = despesas_dir / "despesas_123.json"
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(registro, f, ensure_ascii=False)
                f.write("\n")

            conversor = ConversorDespesasCSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_path = base / "data" / "csv" / "despesas.csv"
            self.assertTrue(csv_path.exists())

            with open(csv_path, encoding="utf-8") as f:
                linhas = list(csv.reader(f))

            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[1][0], "123")
            self.assertEqual(linhas[1][6], "Fornecedor Exemplo")


if __name__ == "__main__":
    unittest.main()
