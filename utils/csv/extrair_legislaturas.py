from pathlib import Path
from typing import Any, Dict, List
from utils.csv.gera_csv import GeradorCSVBase

class ConversorLegislaturasCSV(GeradorCSVBase):
    """
    Especialização para extrair os dados de referência das legislaturas.
    Lê o arquivo `legislaturas.json` e exporta para a dimensão `dim_legislaturas.csv`.
    """

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/legislaturas", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir),
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="dim_legislaturas.csv",
            nome_logger="br_etl.dim_legislaturas",
            log_dir=log_dir
        )

    def obter_padrao_busca_arquivos(self) -> str:
        """
        busca o arquivo de legislaturas.
        """
        return "legislaturas.json"

    def obter_cabecalho_csv(self) -> List[str]:
        """Ordem dascolunas de saída para a dimensão."""
        return ["id", "dataInicio", "dataFim"]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        """Não há variáveis ambientais a serem extraídas do nome deste arquivo."""
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        """
        A tradução final: transforma JSON em CSV.
        """
        return [
            dados_json.get("id"),
            dados_json.get("dataInicio"),
            dados_json.get("dataFim")
        ]
