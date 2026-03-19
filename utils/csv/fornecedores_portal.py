from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorFornecedoresPortalCSV(GeradorCSVBase):
    """Gera a dimensão simplificada de fornecedores do Portal da Transparência."""

    def __init__(
        self,
        data_dir: str = "data",
        output_dir: str = "data/csv/portal_transparencia/dimensoes",
        log_dir: str = "logs",
    ):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "portal_transparencia" / "dimensoes",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="dim_fornecedores.csv",
            nome_logger="br_etl.portal_dim_fornecedores_csv",
            log_dir=log_dir,
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "fornecedores.jsonl"

    def obter_cabecalho_csv(self) -> List[str]:
        return ["documento", "tipo_documento", "cnpj_base", "nome_principal"]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        return [
            dados_json.get("documento"),
            dados_json.get("tipo_documento"),
            dados_json.get("cnpj_base"),
            dados_json.get("nome_principal"),
        ]
