from pathlib import Path
from typing import Any, Dict

from utils.csv.orcamento_item_despesa_siop import ConversorOrcamentoItemDespesaSIOPCSV


class ConversorParticoesOrcamentoItemDespesaSIOPCSV(ConversorOrcamentoItemDespesaSIOPCSV):
    """Gera um CSV para cada arquivo de partição do SIOP, preservando a árvore de anos."""

    def __init__(
        self,
        data_dir: str = "data",
        output_dir: str = "data/csv/siop/orcamento_item_despesa_particoes",
        log_dir: str = "logs",
    ):
        super().__init__(data_dir=data_dir, output_dir=output_dir, log_dir=log_dir)
        self.diretorio_entrada = Path(data_dir) / "orcamento_item_despesa" / "_particoes"

    def obter_padrao_busca_arquivos(self) -> str:
        return "ano=*/funcao=*.json"

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        ano = caminho_arquivo.parent.name.removeprefix("ano=")
        codigo_funcao = caminho_arquivo.stem.removeprefix("funcao=")
        return {"ano_arquivo": ano, "codigo_funcao_arquivo": codigo_funcao}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]):
        linha = super().mapear_linha_json_para_csv(dados_json, metadados_arquivo)
        linha[1] = dados_json.get("codigo_funcao", metadados_arquivo["codigo_funcao_arquivo"])
        return linha

    def obter_caminho_saida_arquivo(self, caminho_arquivo: Path) -> Path:
        relativo = caminho_arquivo.relative_to(self.diretorio_entrada).with_suffix(".csv")
        return self.diretorio_saida / relativo
