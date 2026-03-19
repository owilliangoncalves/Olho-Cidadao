from pathlib import Path
import re
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorDespesasCSV(GeradorCSVBase):
    """Implementação específica para consolidar as despesas dos deputados federais."""

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/despesas", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "despesas_deputados_federais",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="despesas.csv",
            nome_logger="br_etl.despesas_csv",
            log_dir=log_dir
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "**/*.json"

    def obter_cabecalho_csv(self) -> List[str]:
        return [
            "id_deputado", "id_legislatura", "nome_deputado",
            "sigla_uf_deputado", "sigla_partido_deputado", "nomeFornecedor",
            "cnpjCpfFornecedor", "documento_fornecedor_normalizado",
            "tipo_documento_fornecedor", "cnpj_base_fornecedor", "valorLiquido",
            "ano", "mes", "tipoDespesa",
        ]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        match = re.search(r"_(\d+)\.json$", caminho_arquivo.name)
        return {"id_deputado": match.group(1) if match else "desconhecido"}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        return [
            dados_json.get("id_deputado", metadados_arquivo["id_deputado"]),
            dados_json.get("id_legislatura"),
            dados_json.get("nome_deputado"),
            dados_json.get("sigla_uf_deputado"),
            dados_json.get("sigla_partido_deputado"),
            dados_json.get("nomeFornecedor"),
            dados_json.get("cnpjCpfFornecedor"),
            dados_json.get("documento_fornecedor_normalizado"),
            dados_json.get("tipo_documento_fornecedor"),
            dados_json.get("cnpj_base_fornecedor"),
            dados_json.get("valorLiquido"),
            dados_json.get("ano"),
            dados_json.get("mes"),
            dados_json.get("tipoDespesa"),
        ]
