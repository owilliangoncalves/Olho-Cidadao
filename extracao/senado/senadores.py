"""Extrator de despesas CEAPS do Senado Federal."""

import json
from pathlib import Path
from typing import Any

from extracao.extrator_da_base import ExtratorBase
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from utils.documentos import base_cnpj
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.documentos import normalizar_documento
from utils.documentos import tipo_documento

class ExtratorDadosSenado(ExtratorBase):
    """Extrai o endpoint de despesas do Senado e salva por ano.

    O Senado entrega o CEAPS por exercício, então a unidade de persistência
    escolhida é um arquivo JSON Lines por ano em `data/senadores/`.
    """

    def __init__(self, nome_endpoint: str, configuracao: dict):
        """Configura o endpoint e o intervalo de anos a processar."""

        super().__init__(orgao="senado")

        self.nome_endpoint = nome_endpoint
        self.configuracao = configuracao
        self.endpoint = configuracao["endpoint"]
        self.ano_inicio = configuracao["ano_inicio"]
        self.ano_fim = configuracao["ano_fim"]
        self.pasta_destino = Path("data/senadores")
        self.required_output_keys = {
            "documento_fornecedor_normalizado",
            "tipo_documento_fornecedor",
            "cnpj_base_fornecedor",
            "orgao_origem",
            "endpoint_origem",
            "ano_arquivo",
        }

    def _iterar_despesas(self, dados: Any):
        """Normaliza a estrutura da resposta em um iterador de despesas."""

        if not dados:
            return

        despesas = dados
        if isinstance(dados, dict):
            despesas = dados.get("ListaDespesas", {}).get("Despesas", [])

        if isinstance(despesas, dict):
            yield despesas
            return

        if isinstance(despesas, list):
            for item in despesas:
                if isinstance(item, dict):
                    yield item

    def _enriquecer_registro(self, item: dict, ano: int) -> dict:
        """Adiciona chaves derivadas úteis para joins futuros."""

        documento = normalizar_documento(item.get("cpfCnpj"))

        item["documento_fornecedor_normalizado"] = documento
        item["tipo_documento_fornecedor"] = tipo_documento(documento)
        item["cnpj_base_fornecedor"] = base_cnpj(documento)
        item["orgao_origem"] = "senado"
        item["endpoint_origem"] = self.nome_endpoint
        item["ano_arquivo"] = ano

        return item

    def _arquivo_saida(self, ano: int) -> Path:
        """Retorna o caminho final de saída do ano informado."""

        return self.pasta_destino / f"ceaps_{ano}.json"

    def _arquivo_temporario(self, ano: int) -> Path:
        """Retorna o arquivo temporário usado na escrita atômica."""

        return self.pasta_destino / f"ceaps_{ano}.json.tmp"

    def _arquivo_empty(self, ano: int) -> Path:
        """Retorna o marcador de ano vazio."""

        return self.pasta_destino / f"ceaps_{ano}.json.empty"

    def _arquivo_estado(self, ano: int) -> Path:
        """Retorna o arquivo de estado do ano informado."""

        return Path("data/_estado/senado") / f"ceaps_{ano}.state.json"

    def _arquivo_pronto(self, ano: int) -> bool:
        """Indica se já existe um arquivo final reaproveitável para o ano."""

        caminho = self._arquivo_saida(ano)
        return arquivo_jsonl_tem_chaves(caminho, self.required_output_keys)

    def _estado_inicial(self) -> dict:
        """Retorna o estado inicial da tarefa anual."""

        return {
            "status": "pending",
            "attempts": 0,
            "records": 0,
        }

    def _iterar_anos(self):
        """Itera os anos do mais recente para o mais antigo."""

        return range(self.ano_fim, self.ano_inicio - 1, -1)

    def _executar_ano(
        self,
        ano: int,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ) -> str:
        """Executa um exercício do CEAPS com uma retentativa de `.empty`."""

        if self._arquivo_pronto(ano):
            self.logger.info("[%s] Ano %s ja existe, pulando.", self.orgao, ano)
            return "skipped"

        arquivo_empty = self._arquivo_empty(ano)
        retrying_from_empty = _from_empty_retry
        if arquivo_empty.exists():
            if _allow_empty_retry and self._consumir_retry_empty(
                arquivo_empty,
                contexto=f"senado:ceaps:{ano}",
            ):
                retrying_from_empty = True
            else:
                self.logger.info("[%s] Ano %s ja foi marcado como vazio, pulando.", self.orgao, ano)
                return "skipped_empty"

        caminho_estado = self._arquivo_estado(ano)
        estado = carregar_estado_json(caminho_estado, self._estado_inicial())
        estado["status"] = "running"
        estado["attempts"] = int(estado.get("attempts") or 0) + 1
        salvar_estado_json(caminho_estado, estado)

        url_ano = self.endpoint.format(ano=ano)

        try:
            self.logger.info("[%s] Processando ano: %s", self.orgao, ano)

            resposta = self._fazer_requisicao(url_ano, delay=0)
            total = self._salvar_dados(ano, self._iterar_despesas(resposta))

            if total == 0:
                limpar_artefatos(caminho_estado, self._arquivo_temporario(ano))
                if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                    arquivo_empty,
                    contexto=f"senado:ceaps:{ano}",
                ):
                    return self._executar_ano(
                        ano,
                        _allow_empty_retry=False,
                        _from_empty_retry=True,
                    )

                if not _from_empty_retry:
                    arquivo_empty.touch()
                elif arquivo_empty.exists():
                    arquivo_empty.unlink()
                salvar_estado_json(
                    caminho_estado,
                    {
                        **estado,
                        "status": "empty",
                        "records": 0,
                    },
                )
                self.logger.warning("[%s] Nenhum registro encontrado para o ano %s", self.orgao, ano)
                return "empty"

            if arquivo_empty.exists():
                arquivo_empty.unlink()

            limpar_artefatos(caminho_estado)
            self.logger.info("[%s] Ano %s concluido com %s registros.", self.orgao, ano, total)
            return "success"

        except Exception as exc:
            salvar_estado_json(
                caminho_estado,
                {
                    **estado,
                    "status": "error",
                    "message": str(exc)[:1000],
                },
            )
            self.logger.exception("[%s] Falha critica no ano %s", self.orgao, ano)
            return "error"

    def _salvar_dados(self, ano: int, registros) -> int:
        """Grava o resultado do ano em arquivo temporário e promove no final."""

        self.pasta_destino.mkdir(parents=True, exist_ok=True)

        caminho_final = self._arquivo_saida(ano)
        caminho_tmp = self._arquivo_temporario(ano)

        if caminho_tmp.exists():
            caminho_tmp.unlink()

        total = 0

        try:
            # A escrita em arquivo temporário evita deixar saída parcial em caso
            # de interrupção no meio da serialização.
            with open(caminho_tmp, "w", encoding="utf-8") as f:
                for item in registros:
                    json.dump(self._enriquecer_registro(item, ano), f, ensure_ascii=False)
                    f.write("\n")
                    total += 1

            if total == 0:
                if caminho_tmp.exists():
                    caminho_tmp.unlink()
                return 0

            caminho_tmp.replace(caminho_final)
            self.logger.info(
                "[%s] Arquivo salvo em: %s | registros=%s",
                self.orgao,
                caminho_final,
                total,
            )
            return total
        except Exception:
            if caminho_tmp.exists():
                caminho_tmp.unlink()
            raise

    def executar(self):
        """Percorre os anos configurados e processa o CEAPS de cada exercício."""

        self.logger.info(
            "[%s] Iniciando processamento de %s ate %s",
            self.orgao,
            self.ano_inicio,
            self.ano_fim,
        )

        stats = {
            "completed": 0,
            "skipped": 0,
            "empty": 0,
            "failed": 0,
        }

        for ano in self._iterar_anos():
            status = self._executar_ano(ano)
            if status == "success":
                stats["completed"] += 1
            elif status in {"skipped", "skipped_empty"}:
                stats["skipped"] += 1
            elif status == "empty":
                stats["empty"] += 1
            elif status == "error":
                stats["failed"] += 1

        self.logger.info(
            "[%s] Extracao concluida | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            self.orgao,
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
