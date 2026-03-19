import csv
from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorOrcamentoItemDespesaSIOPCSV(GeradorCSVBase):
    """Gera uma tabela fato CSV para cada arquivo anual de itens de despesa do SIOP."""

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/siop/orcamento_item_despesa", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "orcamento_item_despesa",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="fato_orcamento_item_despesa.csv",
            nome_logger="br_etl.siop_orcamento_item_despesa_csv",
            log_dir=log_dir,
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "orcamento_item_despesa_*.json"

    def obter_cabecalho_csv(self) -> List[str]:
        return [
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

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        ano = caminho_arquivo.stem.rsplit("_", maxsplit=1)[-1]
        return {"ano_arquivo": ano}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        return [
            dados_json.get("ano", metadados_arquivo["ano_arquivo"]),
            dados_json.get("codigo_funcao"),
            dados_json.get("codigo_subfuncao"),
            dados_json.get("codigo_programa"),
            dados_json.get("codigo_acao"),
            dados_json.get("codigo_unidade_orcamentaria"),
            dados_json.get("codigo_fonte"),
            dados_json.get("codigo_gnd"),
            dados_json.get("codigo_modalidade"),
            dados_json.get("codigo_elemento"),
            dados_json.get("orgao_origem"),
            dados_json.get("valor_pago"),
            dados_json.get("valor_empenhado"),
            dados_json.get("valor_liquidado"),
        ]

    def obter_caminho_saida_arquivo(self, caminho_arquivo: Path) -> Path:
        """Define o caminho do CSV gerado a partir do arquivo de entrada."""
        return self.diretorio_saida / f"{caminho_arquivo.stem}.csv"

    def executar(self):
        """Gera um CSV independente para cada arquivo `orcamento_item_despesa_<ano>.json`."""

        arquivos = self.listar_arquivos_entrada()

        if not arquivos:
            self.logger.warning("Nenhum arquivo encontrado em %s com o padrão definido.", self.diretorio_entrada)
            return

        self.diretorio_saida.mkdir(parents=True, exist_ok=True)

        for arquivo in arquivos:
            metadados = self.extrair_metadados_arquivo(arquivo)
            arquivo_saida = self.obter_caminho_saida_arquivo(arquivo)
            arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
            self.logger.info("Processando arquivo: %s | Saida: %s", arquivo.name, arquivo_saida.name)

            try:
                with open(arquivo_saida, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(self.obter_cabecalho_csv())

                    for _, dados in self.iterar_registros_arquivo(arquivo):
                        writer.writerow(self.mapear_linha_json_para_csv(dados, metadados))
            except Exception as exc:
                self.logger.error("Erro fatal ao processar o arquivo %s: %s", arquivo, exc)

        self.logger.info("CSVs de itens de despesa gerados com sucesso em: %s", self.diretorio_saida)
