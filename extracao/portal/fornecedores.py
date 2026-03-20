"""Constrói a dimensão local de fornecedores usada pelo pipeline do Portal."""

import csv
import json
from collections import Counter
from pathlib import Path

from configuracao.logger import logger
from extracao.portal.config import PORTAL_FORNECEDORES_PATH
from extracao.portal.config import PortalFornecedoresConfig
from utils.documentos import base_cnpj
from utils.documentos import normalizar_documento
from utils.documentos import tipo_documento


def _iterar_jsonl(arquivos):
    """Itera linhas JSON válidas de um conjunto de arquivos JSON Lines."""

    for arquivo in arquivos:
        with open(arquivo, encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                try:
                    yield json.loads(linha)
                except json.JSONDecodeError:
                    continue


class ConstrutorDimFornecedoresPortal:
    """Consolida fornecedores observados na Câmara e no Senado.

    A dimensão resultante serve como lista de seed para os extratores do
    Portal da Transparência, permitindo priorizar apenas documentos já
    relevantes para o restante do projeto.
    """

    def __init__(
        self,
        output_path: str | Path = PORTAL_FORNECEDORES_PATH,
    ):
        """Define onde a dimensão consolidada será persistida."""

        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.tmp_path = self.output_path.with_suffix(".jsonl.tmp")

    def _iterar_camara_csv(self):
        """Lê fornecedores a partir do CSV consolidado da Câmara, se existir."""

        caminho = Path("data/csv/despesas.csv")
        if not caminho.exists():
            return

        with open(caminho, encoding="utf-8") as f:
            leitor = csv.DictReader(f)
            for row in leitor:
                yield {
                    "documento": row.get("cnpjCpfFornecedor"),
                    "nome": row.get("nomeFornecedor"),
                    "ano": row.get("ano"),
                    "origem": "camara",
                }

    def _iterar_camara_raw(self):
        """Lê fornecedores diretamente dos JSONs de despesas da Câmara."""

        caminho = Path("data/despesas_deputados_federais")
        if not caminho.exists():
            return

        for row in _iterar_jsonl(sorted(caminho.glob("**/*.json"))):
            yield {
                "documento": row.get("cnpjCpfFornecedor"),
                "nome": row.get("nomeFornecedor"),
                "ano": row.get("ano"),
                "origem": "camara",
            }

    def _iterar_senado(self):
        """Lê fornecedores presentes nos arquivos anuais do Senado."""

        caminho = Path("data/senadores")
        if not caminho.exists():
            return

        nome_keys = ("fornecedor", "nomeFornecedor", "razaoSocial")
        doc_keys = ("cnpjCpfFornecedor", "cpfCnpjFornecedor", "cnpjFornecedor")

        for arquivo in sorted(caminho.glob("ceaps_*.json")):
            ano_arquivo = arquivo.stem.split("_")[-1]
            for row in _iterar_jsonl((arquivo,)):
                nome = next((row.get(chave) for chave in nome_keys if row.get(chave)), None)
                documento = next((row.get(chave) for chave in doc_keys if row.get(chave)), None)
                ano = row.get("ano") or ano_arquivo

                yield {
                    "documento": documento,
                    "nome": nome,
                    "ano": ano,
                    "origem": "senado",
                }

    def _iterar_registros(self):
        """Itera os registros de fornecedores a partir das fontes locais disponíveis."""

        csv_path = Path("data/csv/despesas.csv")

        # O CSV consolidado reduz custo de leitura. Quando ele ainda não existe,
        # o builder faz fallback para os JSONs brutos da Câmara.
        if csv_path.exists():
            yield from self._iterar_camara_csv() or []
        else:
            yield from self._iterar_camara_raw() or []

        yield from self._iterar_senado() or []

    def construir(self, min_ocorrencias: int | None = None):
        """Reconstrói a dimensão consolidada de fornecedores.

        Args:
            min_ocorrencias: Quantidade mínima de aparições exigida para manter
                um fornecedor na dimensão final.

        Returns:
            Caminho do arquivo JSON Lines gerado.
        """

        cfg = PortalFornecedoresConfig.carregar(min_ocorrencias=min_ocorrencias)
        fornecedores = {}

        for row in self._iterar_registros():
            documento = normalizar_documento(row.get("documento"))
            if documento is None:
                continue

            fornecedor = fornecedores.setdefault(
                documento,
                {
                    "documento": documento,
                    "tipo_documento": tipo_documento(documento),
                    "nomes": Counter(),
                    "fontes": Counter(),
                    "anos": set(),
                    "total_ocorrencias": 0,
                },
            )

            nome = (row.get("nome") or "").strip()
            if nome:
                fornecedor["nomes"][nome] += 1

            origem = row.get("origem") or "desconhecida"
            fornecedor["fontes"][origem] += 1

            ano = str(row.get("ano") or "").strip()
            if ano.isdigit():
                fornecedor["anos"].add(int(ano))

            fornecedor["total_ocorrencias"] += 1

        registros = []

        for fornecedor in fornecedores.values():
            if fornecedor["total_ocorrencias"] < cfg.min_ocorrencias:
                continue

            nomes_ordenados = fornecedor["nomes"].most_common()
            principal = nomes_ordenados[0][0] if nomes_ordenados else None

            registros.append(
                {
                    "documento": fornecedor["documento"],
                    "tipo_documento": fornecedor["tipo_documento"],
                    "cnpj_base": base_cnpj(fornecedor["documento"]),
                    "nome_principal": principal,
                    "nomes_alternativos": [nome for nome, _ in nomes_ordenados[:5]],
                    "fontes": dict(fornecedor["fontes"]),
                    "anos": sorted(fornecedor["anos"], reverse=True),
                    "total_ocorrencias": fornecedor["total_ocorrencias"],
                }
            )

        registros.sort(
            key=lambda item: (
                -item["total_ocorrencias"],
                item["documento"],
            )
        )

        if self.tmp_path.exists():
            self.tmp_path.unlink()

        with open(self.tmp_path, "w", encoding="utf-8") as f:
            for item in registros:
                json.dump(item, f, ensure_ascii=False)
                f.write("\n")

        self.tmp_path.replace(self.output_path)

        logger.info(
            "[PORTAL] Dimensao de fornecedores atualizada | registros=%s | arquivo=%s",
            len(registros),
            self.output_path,
        )
        return self.output_path

    def carregar(self):
        """Lê a dimensão persistida e retorna seus registros em memória."""

        if not self.output_path.exists():
            return []

        registros = []
        with open(self.output_path, encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                try:
                    registros.append(json.loads(linha))
                except json.JSONDecodeError:
                    continue
        return registros
