from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase

class ConversorDeputadosLegislaturaCSV(GeradorCSVBase):
    """
    Especialização para extrair dados básicos dos deputados agrupados por legislatura.
    Lê de `data/deputados_por_legislaturas` e exporta para `tb_dep_legislatura.csv`.
    """

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/deputados_legislatura", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "deputados_por_legislaturas",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="tb_dep_legislatura.csv",
            nome_logger="br_etl.deputados_legislatura",
            log_dir=log_dir
        )

    def obter_padrao_busca_arquivos(self) -> str:
        """Busca qualquer arquivo JSON dentro do diretório e subdiretórios."""
        return "**/*.json"

    def obter_cabecalho_csv(self) -> List[str]:
        """Define o 'sequenciamento' exato das colunas de saída."""
        return ["id", "nome", "siglaPartido", "siglaUF", "idLegislatura"]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        """
        Órgão vestigial neste contexto: como toda a informação necessária 
        já está dentro do próprio JSON, não precisamos extrair nada do nome do arquivo.
        """
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        """
        A síntese propriamente dita: pega o dicionário JSON e o traduz para a linha do CSV.
        """
        return [
            dados_json.get("id"),
            dados_json.get("nome"),
            dados_json.get("siglaPartido"),
            dados_json.get("siglaUf"), 
            dados_json.get("idLegislatura")
        ]
