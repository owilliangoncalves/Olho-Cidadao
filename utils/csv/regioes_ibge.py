from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorRegioesIBGECSV(GeradorCSVBase):
    """Gera a dimensão de regiões do IBGE."""

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/ibge", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "ibge" / "localidades",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="dim_regioes.csv",
            nome_logger="br_etl.ibge_regioes_csv",
            log_dir=log_dir,
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "regioes.json"

    def obter_cabecalho_csv(self) -> List[str]:
        return ["id", "sigla", "nome"]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        payload = dados_json.get("payload", {})
        return [payload.get("id"), payload.get("sigla"), payload.get("nome")]
