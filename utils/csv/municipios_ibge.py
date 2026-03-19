from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorMunicipiosIBGECSV(GeradorCSVBase):
    """Gera a dimensão de municípios do IBGE."""

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/ibge", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "ibge" / "localidades",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="dim_municipios.csv",
            nome_logger="br_etl.ibge_municipios_csv",
            log_dir=log_dir,
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "municipios.json"

    def obter_cabecalho_csv(self) -> List[str]:
        return [
            "id",
            "nome",
            "uf_id",
            "uf_sigla",
            "uf_nome",
            "regiao_id",
            "regiao_sigla",
            "regiao_nome",
            "mesorregiao_id",
            "mesorregiao_nome",
            "microrregiao_id",
            "microrregiao_nome",
            "regiao_intermediaria_id",
            "regiao_intermediaria_nome",
            "regiao_imediata_id",
            "regiao_imediata_nome",
        ]

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        payload = dados_json.get("payload", {})
        microrregiao = payload.get("microrregiao", {})
        mesorregiao = microrregiao.get("mesorregiao", {})
        uf = mesorregiao.get("UF", {})
        regiao = uf.get("regiao", {})
        regiao_imediata = payload.get("regiao-imediata", {})
        regiao_intermediaria = regiao_imediata.get("regiao-intermediaria", {})

        return [
            payload.get("id"),
            payload.get("nome"),
            uf.get("id"),
            uf.get("sigla"),
            uf.get("nome"),
            regiao.get("id"),
            regiao.get("sigla"),
            regiao.get("nome"),
            mesorregiao.get("id"),
            mesorregiao.get("nome"),
            microrregiao.get("id"),
            microrregiao.get("nome"),
            regiao_intermediaria.get("id"),
            regiao_intermediaria.get("nome"),
            regiao_imediata.get("id"),
            regiao_imediata.get("nome"),
        ]
