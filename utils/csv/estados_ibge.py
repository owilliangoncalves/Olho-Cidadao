from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorEstadosIBGECSV(GeradorCSVBase):
    """Gera a dimensão de estados do IBGE."""

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/ibge", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "ibge" / "localidades",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="dim_estados.csv",
            nome_logger="br_etl.ibge_estados_csv",
            log_dir=log_dir,
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "estados.json"

    def obter_cabecalho_csv(self) -> List[str]:
        return ["id", "sigla", "nome", "regiao_id", "regiao_sigla", "regiao_nome"]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        payload = dados_json.get("payload", {})
        regiao = payload.get("regiao", {})
        return [
            payload.get("id"),
            payload.get("sigla"),
            payload.get("nome"),
            regiao.get("id"),
            regiao.get("sigla"),
            regiao.get("nome"),
        ]
