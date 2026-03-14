"""Extrator da lista mestre de legislaturas da Câmara dos Deputados."""

from __future__ import annotations

import json
from pathlib import Path

from configuracao.endpoint import obter_configuracao_endpoint
from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.paginacao import proxima_pagina


class ExtratorLegislaturas(ExtratorBase):
    """Baixa as legislaturas e grava o resultado em JSON Lines.

    Este extrator segue a estratégia de retomada padronizada do projeto:
    arquivo final, temporário `.tmp`, marcador `.empty` e checkpoint
    `.state.json`.
    """

    def __init__(self, arquivo_saida: str | None = None):
        """Define os caminhos de saída e artefatos de retomada."""

        super().__init__("camara")
        config_extrator = obter_parametros_extrator("camara.legislaturas")
        self.configuracao_endpoint = obter_configuracao_endpoint("legislaturas")
        nome_arquivo = (
            arquivo_saida
            if arquivo_saida is not None
            else config_extrator.get("arquivo_saida", self.configuracao_endpoint["salvar_como"])
        )
        self.arquivo_saida = Path("data") / nome_arquivo
        self.arquivo_tmp = self.arquivo_saida.with_suffix(".json.tmp")
        self.arquivo_empty = self.arquivo_saida.with_suffix(".json.empty")
        self.arquivo_estado = Path("data/_estado/camara/legislaturas.state.json")
        self.required_output_keys = {"id", "dataInicio", "dataFim"}

    def _estado_inicial(self, url: str, params: dict) -> dict:
        """Retorna o estado inicial de paginação do extrator."""

        return {
            "page": 1,
            "pages": 0,
            "records": 0,
            "next_url": url,
            "params": params,
        }

    def _arquivo_pronto(self) -> bool:
        """Indica se o arquivo final já está íntegro no esquema esperado."""

        return arquivo_jsonl_tem_chaves(self.arquivo_saida, self.required_output_keys)

    def executar(
        self,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Percorre todas as páginas do endpoint de legislaturas com retomada."""

        url_inicial = f"{self.base_url}{self.configuracao_endpoint['endpoint']}"
        params_iniciais = {"itens": self.configuracao_endpoint["itens"]}
        retrying_from_empty = _from_empty_retry

        self.logger.info("Iniciando extração da lista mestre de legislaturas.")

        if self._arquivo_pronto():
            self.logger.info("Lista de legislaturas já existe, pulando.")
            return

        if self.arquivo_empty.exists():
            if _allow_empty_retry and self._consumir_retry_empty(
                self.arquivo_empty,
                contexto="camara:legislaturas",
            ):
                retrying_from_empty = True
            else:
                self.logger.info("Lista de legislaturas marcada como vazia, pulando.")
                return

        estado = carregar_estado_json(
            self.arquivo_estado,
            self._estado_inicial(url_inicial, params_iniciais),
        )

        if estado["page"] > 1 and not self.arquivo_tmp.exists():
            estado = self._estado_inicial(url_inicial, params_iniciais)

        if estado["page"] == 1 and self.arquivo_tmp.exists():
            self.arquivo_tmp.unlink()

        if estado.get("next_url") is None and estado.get("records", 0) > 0 and self.arquivo_tmp.exists():
            self.arquivo_tmp.replace(self.arquivo_saida)
            limpar_artefatos(self.arquivo_estado)
            return

        self.arquivo_tmp.parent.mkdir(parents=True, exist_ok=True)
        modo = "a" if estado["records"] > 0 and self.arquivo_tmp.exists() else "w"
        pagina = int(estado["page"])
        paginas_escritas = int(estado["pages"])
        total_registros = int(estado["records"])
        url = estado["next_url"]
        params = estado.get("params")

        with open(self.arquivo_tmp, modo, encoding="utf-8") as f:
            while url:
                self.logger.info("Legislaturas - extraindo página %s", pagina)

                resposta = self._fazer_requisicao(url, params=params, delay=0)
                dados = resposta.get("dados", [])

                if not dados:
                    break

                for registro in dados:
                    json.dump(registro, f, ensure_ascii=False)
                    f.write("\n")

                f.flush()
                total_registros += len(dados)
                paginas_escritas += 1
                pagina += 1
                url = proxima_pagina(resposta)
                params = None

                salvar_estado_json(
                    self.arquivo_estado,
                    {
                        "page": pagina,
                        "pages": paginas_escritas,
                        "records": total_registros,
                        "next_url": url,
                        "params": params,
                    },
                )

        if total_registros == 0:
            limpar_artefatos(self.arquivo_estado, self.arquivo_tmp)
            if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                self.arquivo_empty,
                contexto="camara:legislaturas",
            ):
                self.executar(_allow_empty_retry=False, _from_empty_retry=True)
                return
            if not _from_empty_retry:
                self.arquivo_empty.touch()
            elif self.arquivo_empty.exists():
                self.arquivo_empty.unlink()
            self.logger.warning("Nenhuma legislatura encontrada.")
            return

        if self.arquivo_empty.exists():
            self.arquivo_empty.unlink()

        self.arquivo_tmp.replace(self.arquivo_saida)
        limpar_artefatos(self.arquivo_estado)
        self.logger.info("Lista de legislaturas baixada com sucesso.")
