"""Testes para a consolidação CSV da Câmara."""

import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.csv.atas_pncp import ConversorAtasPNCPCSV
from utils.csv.despesas_deputados import ConversorDespesasCSV
from utils.csv.estados_ibge import ConversorEstadosIBGECSV
from utils.csv.fornecedores_portal import ConversorFornecedoresPortalCSV
from utils.csv.municipios_ibge import ConversorMunicipiosIBGECSV
from utils.csv.orcamento_item_despesa_particoes_siop import ConversorParticoesOrcamentoItemDespesaSIOPCSV
from utils.csv.orquestrador_csv import OrquestradorGeracaoCSVs
from utils.csv.orcamento_item_despesa_siop import ConversorOrcamentoItemDespesaSIOPCSV
from utils.csv.regioes_ibge import ConversorRegioesIBGECSV


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
                output_dir=str(base / "data" / "csv" / "despesas"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_path = base / "data" / "csv" / "despesas" / "despesas.csv"
            self.assertTrue(csv_path.exists())

            with open(csv_path, encoding="utf-8") as f:
                linhas = list(csv.reader(f))

            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[1][0], "123")
            self.assertEqual(linhas[1][5], "Fornecedor Exemplo")

    def test_consolidador_ibge_gera_dimensao_regioes(self):
        """O arquivo de regiões do IBGE deve gerar sua própria dimensão."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            localidades_dir = base / "data" / "ibge" / "localidades"
            localidades_dir.mkdir(parents=True)

            with open(localidades_dir / "regioes.json", "w", encoding="utf-8") as f:
                json.dump({"_meta": {"dataset": "regioes"}, "payload": {"id": 1, "sigla": "N", "nome": "Norte"}}, f, ensure_ascii=False)
                f.write("\n")

            conversor = ConversorRegioesIBGECSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "ibge"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_path = base / "data" / "csv" / "ibge" / "dim_regioes.csv"
            self.assertTrue(csv_path.exists())

            with open(csv_path, encoding="utf-8") as f:
                linhas = list(csv.reader(f))

            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[1], ["1", "N", "Norte"])

    def test_consolidador_ibge_gera_dimensao_estados(self):
        """O arquivo de estados do IBGE deve gerar sua própria dimensão."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            localidades_dir = base / "data" / "ibge" / "localidades"
            localidades_dir.mkdir(parents=True)

            with open(localidades_dir / "estados.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "_meta": {"dataset": "estados"},
                        "payload": {
                            "id": 11,
                            "sigla": "RO",
                            "nome": "Rondonia",
                            "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
                        },
                    },
                    f,
                    ensure_ascii=False,
                )
                f.write("\n")

            conversor = ConversorEstadosIBGECSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "ibge"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_path = base / "data" / "csv" / "ibge" / "dim_estados.csv"
            self.assertTrue(csv_path.exists())

            with open(csv_path, encoding="utf-8") as f:
                linhas = list(csv.reader(f))

            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[1], ["11", "RO", "Rondonia", "1", "N", "Norte"])

    def test_consolidador_ibge_gera_dimensao_municipios(self):
        """O arquivo de municípios do IBGE deve gerar sua própria dimensão."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            localidades_dir = base / "data" / "ibge" / "localidades"
            localidades_dir.mkdir(parents=True)

            with open(localidades_dir / "municipios.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "_meta": {"dataset": "municipios"},
                        "payload": {
                            "id": 1100015,
                            "nome": "Alta Floresta D'Oeste",
                            "microrregiao": {
                                "id": 11006,
                                "nome": "Cacoal",
                                "mesorregiao": {
                                    "id": 1102,
                                    "nome": "Leste Rondoniense",
                                    "UF": {
                                        "id": 11,
                                        "sigla": "RO",
                                        "nome": "Rondonia",
                                        "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
                                    },
                                },
                            },
                            "regiao-imediata": {
                                "id": 110005,
                                "nome": "Cacoal",
                                "regiao-intermediaria": {
                                    "id": 1102,
                                    "nome": "Ji-Parana",
                                    "UF": {
                                        "id": 11,
                                        "sigla": "RO",
                                        "nome": "Rondonia",
                                        "regiao": {"id": 1, "sigla": "N", "nome": "Norte"},
                                    },
                                },
                            },
                        },
                    },
                    f,
                    ensure_ascii=False,
                )
                f.write("\n")

            conversor = ConversorMunicipiosIBGECSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "ibge"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_path = base / "data" / "csv" / "ibge" / "dim_municipios.csv"
            self.assertTrue(csv_path.exists())

            with open(csv_path, encoding="utf-8") as f:
                linhas = list(csv.reader(f))

            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[1][0], "1100015")
            self.assertEqual(linhas[1][2], "11")
            self.assertEqual(linhas[1][9], "Leste Rondoniense")
            self.assertEqual(linhas[1][15], "Cacoal")

    def test_consolidador_siop_gera_um_csv_por_arquivo_com_colunas_filtradas(self):
        """Cada arquivo anual do SIOP deve gerar seu próprio CSV com as colunas solicitadas."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            siop_dir = base / "data" / "orcamento_item_despesa"
            siop_dir.mkdir(parents=True)

            registros = {
                "orcamento_item_despesa_2021.json": {
                    "ano": 2021,
                    "codigo_funcao": "01",
                    "codigo_subfuncao": "031",
                    "codigo_programa": "0034",
                    "codigo_acao": "4061",
                    "codigo_unidade_orcamentaria": "02101",
                    "codigo_fonte": "100",
                    "codigo_gnd": "3",
                    "codigo_modalidade": "90",
                    "codigo_elemento": "00",
                    "orgao_origem": "siop",
                    "valor_pago": "0",
                    "valor_empenhado": "0",
                    "valor_liquidado": "0",
                    "campo_ignorado": "nao deve ir para o csv",
                },
                "orcamento_item_despesa_2024.json": {
                    "ano": 2024,
                    "codigo_funcao": "10",
                    "codigo_subfuncao": "122",
                    "codigo_programa": "2000",
                    "codigo_acao": "20TP",
                    "codigo_unidade_orcamentaria": "26101",
                    "codigo_fonte": "144",
                    "codigo_gnd": "4",
                    "codigo_modalidade": "90",
                    "codigo_elemento": "52",
                    "orgao_origem": "siop",
                    "valor_pago": "150.5",
                    "valor_empenhado": "200.0",
                    "valor_liquidado": "175.25",
                },
            }

            for nome_arquivo, registro in registros.items():
                with open(siop_dir / nome_arquivo, "w", encoding="utf-8") as f:
                    json.dump(registro, f, ensure_ascii=False)
                    f.write("\n")

            conversor = ConversorOrcamentoItemDespesaSIOPCSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "siop" / "orcamento_item_despesa"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_2021 = base / "data" / "csv" / "siop" / "orcamento_item_despesa" / "orcamento_item_despesa_2021.csv"
            csv_2024 = base / "data" / "csv" / "siop" / "orcamento_item_despesa" / "orcamento_item_despesa_2024.csv"

            self.assertTrue(csv_2021.exists())
            self.assertTrue(csv_2024.exists())

            with open(csv_2021, encoding="utf-8") as f:
                linhas_2021 = list(csv.reader(f))

            with open(csv_2024, encoding="utf-8") as f:
                linhas_2024 = list(csv.reader(f))

            cabecalho_esperado = [
                "ano",
                "codigo_funcao",
                "codigo_subfuncao",
                "codigo_programa",
                "codigo_acao",
                "codigo_unidade_orcamentaria",
                "codigo_fonte",
                "codigo_gnd",
                "codigo_modalidade",
                "codigo_elemento",
                "orgao_origem",
                "valor_pago",
                "valor_empenhado",
                "valor_liquidado",
            ]

            self.assertEqual(linhas_2021[0], cabecalho_esperado)
            self.assertEqual(
                linhas_2021[1],
                ["2021", "01", "031", "0034", "4061", "02101", "100", "3", "90", "00", "siop", "0", "0", "0"],
            )

            self.assertEqual(linhas_2024[0], cabecalho_esperado)
            self.assertEqual(
                linhas_2024[1],
                ["2024", "10", "122", "2000", "20TP", "26101", "144", "4", "90", "52", "siop", "150.5", "200.0", "175.25"],
            )

    def test_consolidador_siop_gera_um_csv_por_particao_preservando_subpastas(self):
        """Cada partição do SIOP deve gerar um CSV próprio dentro da árvore de anos."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            particoes_dir = base / "data" / "orcamento_item_despesa" / "_particoes"
            (particoes_dir / "ano=2021").mkdir(parents=True)
            (particoes_dir / "ano=2024").mkdir(parents=True)

            registros = {
                particoes_dir / "ano=2021" / "funcao=02.json": {
                    "ano": 2021,
                    "codigo_funcao": "02",
                    "codigo_subfuncao": "122",
                    "codigo_programa": "0033",
                    "codigo_acao": "20GP",
                    "codigo_unidade_orcamentaria": "14101",
                    "codigo_fonte": "1027",
                    "codigo_gnd": "3",
                    "codigo_modalidade": "90",
                    "codigo_elemento": "39",
                    "orgao_origem": "siop",
                    "valor_pago": "16271.85",
                    "valor_empenhado": "16271.85",
                    "valor_liquidado": "16271.85",
                },
                particoes_dir / "ano=2024" / "funcao=10.json": {
                    "ano": 2024,
                    "codigo_subfuncao": "122",
                    "codigo_programa": "2000",
                    "codigo_acao": "20TP",
                    "codigo_unidade_orcamentaria": "26101",
                    "codigo_fonte": "144",
                    "codigo_gnd": "4",
                    "codigo_modalidade": "90",
                    "codigo_elemento": "52",
                    "orgao_origem": "siop",
                    "valor_pago": "150.5",
                    "valor_empenhado": "200.0",
                    "valor_liquidado": "175.25",
                },
            }

            for caminho, registro in registros.items():
                with open(caminho, "w", encoding="utf-8") as f:
                    json.dump(registro, f, ensure_ascii=False)
                    f.write("\n")

            conversor = ConversorParticoesOrcamentoItemDespesaSIOPCSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "siop" / "orcamento_item_despesa_particoes"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_2021 = base / "data" / "csv" / "siop" / "orcamento_item_despesa_particoes" / "ano=2021" / "funcao=02.csv"
            csv_2024 = base / "data" / "csv" / "siop" / "orcamento_item_despesa_particoes" / "ano=2024" / "funcao=10.csv"

            self.assertTrue(csv_2021.exists())
            self.assertTrue(csv_2024.exists())

            with open(csv_2021, encoding="utf-8") as f:
                linhas_2021 = list(csv.reader(f))

            with open(csv_2024, encoding="utf-8") as f:
                linhas_2024 = list(csv.reader(f))

            self.assertEqual(linhas_2021[1][0], "2021")
            self.assertEqual(linhas_2021[1][1], "02")
            self.assertEqual(linhas_2021[1][-1], "16271.85")

            self.assertEqual(linhas_2024[1][0], "2024")
            self.assertEqual(linhas_2024[1][1], "10")
            self.assertEqual(linhas_2024[1][-1], "175.25")

    def test_consolidador_pncp_gera_um_csv_por_arquivo_de_atas(self):
        """Cada arquivo mensal de atas do PNCP deve gerar um CSV próprio com as colunas filtradas."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            atas_dir = base / "data" / "pncp" / "atas"
            (atas_dir / "ano=2025").mkdir(parents=True)
            (atas_dir / "ano=2026").mkdir(parents=True)

            registros = {
                atas_dir / "ano=2025" / "mes=12.json": {
                    "_meta": {
                        "dataset": "atas",
                        "data_inicial": "2025-12-01",
                        "data_final": "2025-12-31",
                        "orgao_origem": "pncp",
                    },
                    "payload": {
                        "numeroControlePNCPAta": "111-1-000001/2025-000001",
                        "numeroAtaRegistroPreco": "ARP-001",
                        "numeroControlePNCPCompra": "111-1-000001/2025",
                        "cancelado": False,
                        "dataCancelamento": None,
                        "dataAssinatura": "2025-12-10",
                        "vigenciaInicio": "2025-12-11",
                        "vigenciaFim": "2026-12-11",
                        "dataPublicacaoPncp": "2025-12-12",
                        "dataInclusao": "2025-12-12",
                        "dataAtualizacao": "2025-12-13",
                        "dataAtualizacaoGlobal": "2025-12-14",
                        "usuario": "Usuario PNCP",
                        "cnpjOrgao": "12345678000199",
                        "nomeOrgao": "ORGAO A",
                        "cnpjOrgaoSubrogado": None,
                        "nomeOrgaoSubrogado": None,
                        "codigoUnidadeOrgao": "1",
                        "nomeUnidadeOrgao": "UNIDADE A",
                        "codigoUnidadeOrgaoSubrogado": None,
                        "nomeUnidadeOrgaoSubrogado": None,
                        "campo_ignorado": "nao vai para o csv",
                    },
                },
                atas_dir / "ano=2026" / "mes=01.json": {
                    "_meta": {
                        "dataset": "atas",
                        "data_inicial": "2026-01-01",
                        "data_final": "2026-01-31",
                        "orgao_origem": "pncp",
                    },
                    "payload": {
                        "numeroControlePNCPAta": "222-1-000001/2026-000001",
                        "numeroAtaRegistroPreco": "ARP-002",
                        "numeroControlePNCPCompra": "222-1-000001/2026",
                        "cancelado": True,
                        "dataCancelamento": "2026-01-15",
                        "dataAssinatura": "2026-01-05",
                        "vigenciaInicio": "2026-01-06",
                        "vigenciaFim": "2027-01-06",
                        "dataPublicacaoPncp": "2026-01-07",
                        "dataInclusao": "2026-01-07",
                        "dataAtualizacao": "2026-01-08",
                        "dataAtualizacaoGlobal": "2026-01-09",
                        "usuario": "Outro Usuario",
                        "cnpjOrgao": "99887766000155",
                        "nomeOrgao": "ORGAO B",
                        "cnpjOrgaoSubrogado": "11223344000100",
                        "nomeOrgaoSubrogado": "ORGAO SUBROGADO",
                        "codigoUnidadeOrgao": "2",
                        "nomeUnidadeOrgao": "UNIDADE B",
                        "codigoUnidadeOrgaoSubrogado": "20",
                        "nomeUnidadeOrgaoSubrogado": "UNIDADE SUBROGADA",
                    },
                },
            }

            for caminho, registro in registros.items():
                with open(caminho, "w", encoding="utf-8") as f:
                    json.dump(registro, f, ensure_ascii=False)
                    f.write("\n")

            conversor = ConversorAtasPNCPCSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "pncp" / "atas"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_2025 = base / "data" / "csv" / "pncp" / "atas" / "ano=2025" / "mes=12.csv"
            csv_2026 = base / "data" / "csv" / "pncp" / "atas" / "ano=2026" / "mes=01.csv"

            self.assertTrue(csv_2025.exists())
            self.assertTrue(csv_2026.exists())

            with open(csv_2025, encoding="utf-8") as f:
                linhas_2025 = list(csv.reader(f))

            with open(csv_2026, encoding="utf-8") as f:
                linhas_2026 = list(csv.reader(f))

            cabecalho_esperado = [
                "data_inicial",
                "data_final",
                "orgao_origem",
                "numeroControlePNCPAta",
                "numeroAtaRegistroPreco",
                "numeroControlePNCPCompra",
                "cancelado",
                "dataCancelamento",
                "dataAssinatura",
                "vigenciaInicio",
                "vigenciaFim",
                "dataPublicacaoPncp",
                "dataInclusao",
                "dataAtualizacao",
                "dataAtualizacaoGlobal",
                "usuario",
                "cnpjOrgao",
                "nomeOrgao",
                "cnpjOrgaoSubrogado",
                "nomeOrgaoSubrogado",
                "codigoUnidadeOrgao",
                "nomeUnidadeOrgao",
                "codigoUnidadeOrgaoSubrogado",
                "nomeUnidadeOrgaoSubrogado",
            ]

            self.assertEqual(linhas_2025[0], cabecalho_esperado)
            self.assertEqual(
                linhas_2025[1],
                [
                    "2025-12-01",
                    "2025-12-31",
                    "pncp",
                    "111-1-000001/2025-000001",
                    "ARP-001",
                    "111-1-000001/2025",
                    "False",
                    "",
                    "2025-12-10",
                    "2025-12-11",
                    "2026-12-11",
                    "2025-12-12",
                    "2025-12-12",
                    "2025-12-13",
                    "2025-12-14",
                    "Usuario PNCP",
                    "12345678000199",
                    "ORGAO A",
                    "",
                    "",
                    "1",
                    "UNIDADE A",
                    "",
                    "",
                ],
            )

            self.assertEqual(linhas_2026[0], cabecalho_esperado)
            self.assertEqual(linhas_2026[1][0], "2026-01-01")
            self.assertEqual(linhas_2026[1][3], "222-1-000001/2026-000001")
            self.assertEqual(linhas_2026[1][6], "True")
            self.assertEqual(linhas_2026[1][18], "11223344000100")
            self.assertEqual(linhas_2026[1][23], "UNIDADE SUBROGADA")

    def test_consolidador_portal_gera_dim_fornecedores_com_colunas_reduzidas(self):
        """A dimensão de fornecedores do Portal deve exportar apenas os campos essenciais."""

        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            dimensoes_dir = base / "data" / "portal_transparencia" / "dimensoes"
            dimensoes_dir.mkdir(parents=True)

            registro = {
                "documento": "17895646000187",
                "tipo_documento": "cnpj",
                "cnpj_base": "17895646",
                "nome_principal": "UBER DO BRASIL TECNOLOGIA LTDA.",
                "fontes": {"camara": 135},
                "anos": [2025, 2024, 2023],
                "total_ocorrencias": 135,
            }

            with open(dimensoes_dir / "fornecedores.jsonl", "w", encoding="utf-8") as f:
                json.dump(registro, f, ensure_ascii=False)
                f.write("\n")

            conversor = ConversorFornecedoresPortalCSV(
                data_dir=str(base / "data"),
                output_dir=str(base / "data" / "csv" / "portal_transparencia" / "dimensoes"),
                log_dir=str(base / "logs"),
            )
            conversor.executar()

            csv_path = base / "data" / "csv" / "portal_transparencia" / "dimensoes" / "dim_fornecedores.csv"
            self.assertTrue(csv_path.exists())

            with open(csv_path, encoding="utf-8") as f:
                linhas = list(csv.reader(f))

            self.assertEqual(
                linhas[0],
                ["documento", "tipo_documento", "cnpj_base", "nome_principal"],
            )
            self.assertEqual(
                linhas[1],
                ["17895646000187", "cnpj", "17895646", "UBER DO BRASIL TECNOLOGIA LTDA."],
            )

    def test_orquestrador_executa_todos_os_geradores_registrados(self):
        """O orquestrador deve instanciar e executar todos os geradores registrados."""

        chamadas = []

        class FakeGeradorA:
            def __init__(self, data_dir: str, output_dir: str, log_dir: str):
                self.data_dir = Path(data_dir)
                self.output_dir = Path(output_dir)
                self.log_dir = Path(log_dir)

            def executar(self):
                chamadas.append(("a", self.data_dir, self.output_dir, self.log_dir))

        class FakeGeradorB:
            def __init__(self, data_dir: str, output_dir: str, log_dir: str):
                self.data_dir = Path(data_dir)
                self.output_dir = Path(output_dir)
                self.log_dir = Path(log_dir)

            def executar(self):
                chamadas.append(("b", self.data_dir, self.output_dir, self.log_dir))

        registros_originais = OrquestradorGeracaoCSVs.GERADORES_CSV

        with TemporaryDirectory() as tmp:
            base = Path(tmp)

            try:
                OrquestradorGeracaoCSVs.GERADORES_CSV = (
                    ("fake_a", FakeGeradorA, Path("grupo_a")),
                    ("fake_b", FakeGeradorB, Path("grupo_b") / "subgrupo"),
                )

                executados = OrquestradorGeracaoCSVs(
                    data_dir=str(base / "data"),
                    output_dir=str(base / "data" / "csv"),
                    log_dir=str(base / "logs"),
                ).executar()
            finally:
                OrquestradorGeracaoCSVs.GERADORES_CSV = registros_originais

        self.assertEqual(executados, ["fake_a", "fake_b"])
        self.assertEqual(
            chamadas,
            [
                ("a", base / "data", base / "data" / "csv" / "grupo_a", base / "logs"),
                ("b", base / "data", base / "data" / "csv" / "grupo_b" / "subgrupo", base / "logs"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
