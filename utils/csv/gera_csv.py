from __future__ import annotations

import csv
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable, List, cast

from configuracao.logger import get_logger


class GeradorCSVBase(ABC):
    """
    Classe base generalista para geração de CSVs a partir de arquivos JSON/JSONL.

    Implementa o padrão Template Method. O fluxo principal fica em `executar()`,
    enquanto as subclasses especializadas definem o formato dos arquivos de
    entrada, cabeçalho e mapeamento de cada registro.
    """

    logger: logging.Logger

    def __init__(
        self,
        diretorio_entrada: str | Path,
        diretorio_saida: str | Path,
        nome_arquivo_saida: str,
        nome_logger: str = "etl.jsonl_para_csv",
        log_dir: str | Path = "logs",
    ):
        self.diretorio_entrada = Path(diretorio_entrada)
        self.diretorio_saida = Path(diretorio_saida)
        self.arquivo_saida = self.diretorio_saida / nome_arquivo_saida
        self.log_dir = Path(log_dir)
        self.nome_logger = nome_logger
        self.logger = get_logger(self.nome_logger)

        self._configurar_logs()

    def _configurar_logs(self):
        """Configura o logger padronizado para o processo."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_dir / f"{self.nome_logger.replace('.', '_')}.log"

        if not any(
            isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_path
            for h in self.logger.handlers
        ):
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
            )
            self.logger.addHandler(handler)

    @abstractmethod
    def obter_padrao_busca_arquivos(self) -> str:
        """Define o padrão glob para buscar os arquivos de entrada."""
        pass

    @abstractmethod
    def obter_cabecalho_csv(self) -> List[str]:
        """Retorna a lista de colunas para o CSV."""
        pass

    @abstractmethod
    def extrair_metadados_arquivo(self, caminho_arquivo: Path) -> Dict[str, Any]:
        """
        Extrai informações úteis do nome/caminho do arquivo (ex: IDs, datas).
        Esses metadados serão passados para a extração de cada linha.
        """
        return {}

    @abstractmethod
    def mapear_linha_json_para_csv(
        self,
        dados_json: Dict[str, Any],
        metadados_arquivo: Dict[str, Any],
    ) -> List[Any]:
        """
        Transforma o dicionário de uma linha JSON em uma lista de valores
        ordenada conforme o cabeçalho do CSV.
        """
        pass

    def listar_arquivos_entrada(self) -> List[Path]:
        """Centraliza a descoberta de arquivos para permitir customizações."""
        return sorted(self.diretorio_entrada.glob(self.obter_padrao_busca_arquivos()))

    def iterar_registros_arquivo(self, caminho_arquivo: Path) -> Iterable[tuple[int, Dict[str, Any]]]:
        """
        Itera registros JSON de um arquivo.

        Por padrão assume um arquivo JSON Lines, mas também aceita um JSON único
        em formato objeto ou lista de objetos.
        """
        with open(caminho_arquivo, encoding="utf-8") as arquivo:
            conteudo = arquivo.read().strip()

        if not conteudo:
            return

        try:
            dados_carregados: object = json.loads(conteudo)
        except json.JSONDecodeError:
            for num_linha, linha_texto in enumerate(conteudo.splitlines(), start=1):
                linha_texto = linha_texto.strip()
                if not linha_texto:
                    continue
                try:
                    linha_dados: object = json.loads(linha_texto)
                    if isinstance(linha_dados, dict):
                        yield num_linha, cast(Dict[str, Any], linha_dados)
                except json.JSONDecodeError as exc:
                    self.logger.warning(
                        "JSON inválido no arquivo %s, linha %d: %s",
                        caminho_arquivo.name,
                        num_linha,
                        exc,
                    )
            return

        if isinstance(dados_carregados, list):
            for indice, item in enumerate(cast(List[Any], dados_carregados), start=1):
                if isinstance(item, dict):
                    yield indice, cast(Dict[str, Any], item)
            return

        if isinstance(dados_carregados, dict):
            yield 1, cast(Dict[str, Any], dados_carregados)

    def executar(self):
        """O processo principal de ETL (Extract, Transform, Load)."""
        arquivos = self.listar_arquivos_entrada()

        if not arquivos:
            self.logger.warning("Nenhum arquivo encontrado em %s com o padrão definido.", self.diretorio_entrada)
            return

        self.diretorio_saida.mkdir(parents=True, exist_ok=True)

        with open(self.arquivo_saida, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.obter_cabecalho_csv())

            for arquivo in arquivos:
                metadados = self.extrair_metadados_arquivo(arquivo)
                self.logger.info("Processando arquivo: %s | Metadados: %s", arquivo.name, metadados)

                try:
                    for num_linha, dados in self.iterar_registros_arquivo(arquivo):
                        try:
                            linha_csv = self.mapear_linha_json_para_csv(dados, metadados)
                            writer.writerow(linha_csv)
                        except Exception as exc:
                            self.logger.warning(
                                "Erro ao processar linha %d do arquivo %s: %s",
                                num_linha,
                                arquivo.name,
                                exc,
                            )
                except Exception as exc:
                    self.logger.error("Erro fatal ao processar o arquivo %s: %s", arquivo, exc)

        self.logger.info("CSV consolidado com sucesso em: %s", self.arquivo_saida)

