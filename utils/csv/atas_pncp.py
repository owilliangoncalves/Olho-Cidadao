import csv
from pathlib import Path
from typing import Any, Dict, List

from utils.csv.gera_csv import GeradorCSVBase


class ConversorAtasPNCPCSV(GeradorCSVBase):
    """Gera um CSV para cada arquivo mensal de atas do PNCP."""

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv/pncp/atas", log_dir: str = "logs"):
        super().__init__(
            diretorio_entrada=Path(data_dir) / "pncp" / "atas",
            diretorio_saida=Path(output_dir),
            nome_arquivo_saida="atas.csv",
            nome_logger="br_etl.pncp_atas_csv",
            log_dir=log_dir,
        )

    def obter_padrao_busca_arquivos(self) -> str:
        return "ano=*/mes=*.json"

    def obter_cabecalho_csv(self) -> List[str]:
        return [
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

    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        return {}

    def mapear_linha_json_para_csv(self, dados_json: Dict[str, Any], metadados_arquivo: Dict[str, Any]) -> List[Any]:
        meta = dados_json.get("_meta", {})
        payload = dados_json.get("payload", {})
        return [
            meta.get("data_inicial"),
            meta.get("data_final"),
            meta.get("orgao_origem"),
            payload.get("numeroControlePNCPAta"),
            payload.get("numeroAtaRegistroPreco"),
            payload.get("numeroControlePNCPCompra"),
            payload.get("cancelado"),
            payload.get("dataCancelamento"),
            payload.get("dataAssinatura"),
            payload.get("vigenciaInicio"),
            payload.get("vigenciaFim"),
            payload.get("dataPublicacaoPncp"),
            payload.get("dataInclusao"),
            payload.get("dataAtualizacao"),
            payload.get("dataAtualizacaoGlobal"),
            payload.get("usuario"),
            payload.get("cnpjOrgao"),
            payload.get("nomeOrgao"),
            payload.get("cnpjOrgaoSubrogado"),
            payload.get("nomeOrgaoSubrogado"),
            payload.get("codigoUnidadeOrgao"),
            payload.get("nomeUnidadeOrgao"),
            payload.get("codigoUnidadeOrgaoSubrogado"),
            payload.get("nomeUnidadeOrgaoSubrogado"),
        ]

    def obter_caminho_saida_arquivo(self, caminho_arquivo: Path) -> Path:
        relativo = caminho_arquivo.relative_to(self.diretorio_entrada).with_suffix(".csv")
        return self.diretorio_saida / relativo

    def executar(self):
        """Gera um CSV independente para cada arquivo mensal de atas do PNCP."""

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

        self.logger.info("CSVs de atas do PNCP gerados com sucesso em: %s", self.diretorio_saida)
