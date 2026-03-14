"""Consolida arquivos JSON Lines de despesas em um CSV analítico único."""

import csv
import json
import logging
import re
from pathlib import Path

from configuracao.logger import get_logger


class ConversorDespesasCSV:
    """Transforma os arquivos de despesas da Câmara em um CSV tabular.

    O conversor assume que os arquivos de entrada seguem o padrão
    `data/despesas_deputados_federais/<ano>/despesas_<id>.json`, com um objeto
    JSON por linha.
    """

    def __init__(self, data_dir: str = "data", output_dir: str = "data", log_dir: str = "logs"):
        """Configura os diretórios de entrada, saída e logging."""

        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir) / "csv"
        self.log_dir = Path(log_dir)
        self.output_file = self.output_dir / "despesas.csv"

        self._configurar_logs()

    def _configurar_logs(self):
        """Inicializa o arquivo de log específico da etapa de consolidação."""

        self.log_dir.mkdir(exist_ok=True)
        self.logger = get_logger("br_etl.csv")
        log_path = self.log_dir / "gera_csv.log"

        if not any(
            isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == log_path
            for handler in self.logger.handlers
        ):
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
            )
            self.logger.addHandler(handler)

    def _extrair_id_do_arquivo(self, nome_arquivo: str) -> str:
        """Extrai o identificador do deputado a partir do nome do arquivo."""

        match = re.search(r"_(\d+)\.json$", nome_arquivo)
        return match.group(1) if match else "desconhecido"

    def executar(self):
        """Percorre os JSONs de despesas e escreve o CSV consolidado."""

        caminho_busca = self.data_dir / "despesas_deputados_federais"
        arquivos = sorted(caminho_busca.glob("**/*.json"))

        if not arquivos:
            self.logger.warning("Nenhum arquivo JSON encontrado em %s", caminho_busca)
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                [
                    "id_deputado",
                    "id_legislatura",
                    "nome_deputado",
                    "uri_deputado",
                    "sigla_uf_deputado",
                    "sigla_partido_deputado",
                    "nomeFornecedor",
                    "cnpjCpfFornecedor",
                    "documento_fornecedor_normalizado",
                    "tipo_documento_fornecedor",
                    "cnpj_base_fornecedor",
                    "valorLiquido",
                    "ano",
                    "mes",
                    "tipoDespesa",
                ]
            )

            for arquivo in arquivos:
                id_deputado = self._extrair_id_do_arquivo(arquivo.name)
                self.logger.info("Processando ID %s: %s", id_deputado, arquivo.name)

                try:
                    with open(arquivo, encoding="utf-8") as f:
                        for linha_texto in f:
                            if not linha_texto.strip():
                                continue

                            dados = json.loads(linha_texto)
                            writer.writerow(
                                [
                                    id_deputado,
                                    dados.get("id_legislatura"),
                                    dados.get("nome_deputado"),
                                    dados.get("uri_deputado"),
                                    dados.get("sigla_uf_deputado"),
                                    dados.get("sigla_partido_deputado"),
                                    dados.get("nomeFornecedor"),
                                    dados.get("cnpjCpfFornecedor"),
                                    dados.get("documento_fornecedor_normalizado"),
                                    dados.get("tipo_documento_fornecedor"),
                                    dados.get("cnpj_base_fornecedor"),
                                    dados.get("valorLiquido"),
                                    dados.get("ano"),
                                    dados.get("mes"),
                                    dados.get("tipoDespesa"),
                                ]
                            )
                except Exception as exc:
                    self.logger.error("Erro ao processar %s: %s", arquivo, exc)

        self.logger.info("CSV consolidado com sucesso em: %s", self.output_file)
