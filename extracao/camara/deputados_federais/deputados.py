"""Extrai a relação de deputados por legislatura da Câmara."""

from __future__ import annotations

import json
from pathlib import Path

from configuracao.endpoint import obter_configuracao_endpoint
from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase
from infra.concorrencia import executar_tarefas_limitadas
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.paginacao import proxima_pagina


class ExtratorDeputadosLegislatura(ExtratorBase):
    """Baixa deputados para cada legislatura listada em `data/legislaturas.json`.

    Cada legislatura é tratada como uma unidade de trabalho independente com
    retomada por arquivo de estado e escrita incremental em arquivo temporário.
    """

    def __init__(
        self,
        arquivo_entrada: str | None = None,
        pasta_saida: str | None = None,
        prefixo_arquivo: str | None = None,
    ):
        """Configura os caminhos de entrada, saída e concorrência."""

        super().__init__("camara")

        config_extrator = obter_parametros_extrator("camara.deputados_legislatura")
        self.configuracao_endpoint = obter_configuracao_endpoint("deputados")
        self.arquivo_entrada = Path(
            arquivo_entrada
            if arquivo_entrada is not None
            else config_extrator.get("arquivo_entrada")
        )
        self.pasta_saida = (
            pasta_saida if pasta_saida is not None else config_extrator.get("pasta_saida")
        )
        self.prefixo_arquivo = (
            prefixo_arquivo
            if prefixo_arquivo is not None
            else config_extrator.get("prefixo_arquivo")
        )
        self.max_workers = config_extrator.get("max_workers")
        self.max_pending = self.max_workers * 4
        self.required_output_keys = {"id", "id_legislatura"}

        (Path("data") / self.pasta_saida).mkdir(parents=True, exist_ok=True)

    def _obter_ids_legislaturas(self):
        """Itera os identificadores de legislatura a partir do arquivo mestre."""

        if not self.arquivo_entrada.exists():
            self.logger.error("Arquivo não encontrado: %s", self.arquivo_entrada)
            return

        with open(self.arquivo_entrada, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue

                try:
                    legislatura = json.loads(linha)
                    yield legislatura["id"]
                except json.JSONDecodeError:
                    self.logger.warning("Linha ignorada: falha ao decodificar JSON.")

    def _arquivo_saida(self, id_leg: int) -> Path:
        """Resolve o caminho do arquivo final da legislatura."""

        return Path("data") / self.pasta_saida / f"{self.prefixo_arquivo}_{id_leg}.json"

    def _arquivo_tmp(self, id_leg: int) -> Path:
        """Retorna o arquivo temporário da legislatura."""

        return self._arquivo_saida(id_leg).with_suffix(".json.tmp")

    def _arquivo_empty(self, id_leg: int) -> Path:
        """Retorna o marcador de saída vazia da legislatura."""

        return self._arquivo_saida(id_leg).with_suffix(".json.empty")

    def _arquivo_estado(self, id_leg: int) -> Path:
        """Retorna o arquivo de estado da legislatura."""

        return Path("data/_estado/camara/deputados_por_legislatura") / f"id={id_leg}.state.json"

    def _arquivo_pronto(self, id_leg: int) -> bool:
        """Indica se a saída da legislatura já está pronta para reuso."""

        return arquivo_jsonl_tem_chaves(self._arquivo_saida(id_leg), self.required_output_keys)

    def _estado_inicial(self, url: str, params: dict) -> dict:
        """Retorna o estado inicial de paginação da legislatura."""

        return {
            "page": 1,
            "pages": 0,
            "records": 0,
            "next_url": url,
            "params": params,
        }

    def _processar_legislatura(
        self,
        id_leg: int,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Extrai todas as páginas de deputados de uma legislatura."""

        caminho_saida = self._arquivo_saida(id_leg)
        caminho_tmp = self._arquivo_tmp(id_leg)
        caminho_empty = self._arquivo_empty(id_leg)
        caminho_estado = self._arquivo_estado(id_leg)
        retrying_from_empty = _from_empty_retry

        if self._arquivo_pronto(id_leg):
            self.logger.info("Legislatura %s já existe, pulando.", id_leg)
            return

        if caminho_empty.exists():
            if _allow_empty_retry and self._consumir_retry_empty(
                caminho_empty,
                contexto=f"deputados_legislatura:{id_leg}",
            ):
                retrying_from_empty = True
            else:
                self.logger.info("Legislatura %s já foi marcada como vazia, pulando.", id_leg)
                return

        url_inicial = f"{self.base_url}{self.configuracao_endpoint['endpoint'].format(id=id_leg)}"
        params_iniciais = {"itens": self.configuracao_endpoint["itens"]}
        estado = carregar_estado_json(
            caminho_estado,
            self._estado_inicial(url_inicial, params_iniciais),
        )

        if estado["page"] > 1 and not caminho_tmp.exists():
            estado = self._estado_inicial(url_inicial, params_iniciais)

        if estado["page"] == 1 and caminho_tmp.exists():
            caminho_tmp.unlink()

        if estado.get("next_url") is None and estado.get("records", 0) > 0 and caminho_tmp.exists():
            caminho_tmp.replace(caminho_saida)
            limpar_artefatos(caminho_estado)
            return

        pagina = int(estado["page"])
        paginas_escritas = int(estado["pages"])
        total_registros = int(estado["records"])
        url = estado["next_url"]
        params = estado.get("params")
        modo = "a" if total_registros > 0 and caminho_tmp.exists() else "w"

        with open(caminho_tmp, modo, encoding="utf-8") as f:
            while url:
                self.logger.info("Legislatura %s - página %s", id_leg, pagina)

                resposta = self._fazer_requisicao(url, params, delay=0)
                dados = resposta.get("dados", [])

                if not dados:
                    break

                for registro in dados:
                    registro["id_legislatura"] = id_leg
                    json.dump(registro, f, ensure_ascii=False)
                    f.write("\n")

                f.flush()
                total_registros += len(dados)
                paginas_escritas += 1
                pagina += 1
                url = proxima_pagina(resposta)
                params = None

                salvar_estado_json(
                    caminho_estado,
                    {
                        "page": pagina,
                        "pages": paginas_escritas,
                        "records": total_registros,
                        "next_url": url,
                        "params": params,
                    },
                )

        if total_registros == 0:
            limpar_artefatos(caminho_estado, caminho_tmp)
            if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                caminho_empty,
                contexto=f"deputados_legislatura:{id_leg}",
            ):
                self._processar_legislatura(
                    id_leg,
                    _allow_empty_retry=False,
                    _from_empty_retry=True,
                )
                return
            if not _from_empty_retry:
                caminho_empty.touch()
            elif caminho_empty.exists():
                caminho_empty.unlink()
            self.logger.warning("Nenhum deputado encontrado para a legislatura %s.", id_leg)
            return

        if caminho_empty.exists():
            caminho_empty.unlink()

        caminho_tmp.replace(caminho_saida)
        limpar_artefatos(caminho_estado)

    def executar(self):
        """Processa todas as legislaturas com concorrência controlada."""

        self.logger.info("Iniciando extração de deputados por legislatura.")
        enviados = executar_tarefas_limitadas(
            self._obter_ids_legislaturas() or [],
            self._processar_legislatura,
            max_workers=self.max_workers,
            max_pending=self.max_pending,
        )

        if enviados == 0:
            self.logger.warning("Nenhuma legislatura encontrada.")
            return

        self.logger.info("Processo de extração finalizado com sucesso.")
