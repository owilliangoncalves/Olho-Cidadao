"""Extrator paginado de despesas da Câmara por deputado e por ano."""

from __future__ import annotations

import json
from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from infra.http.cliente import http_client
from utils.documentos import base_cnpj
from utils.documentos import normalizar_documento
from utils.documentos import tipo_documento
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.paginacao import proxima_pagina
from utils.parametros import resolver_parametros_data


class ExtratorDadosCamara(ExtratorBase):
    """Extrai um endpoint paginado da Câmara e persiste a saída em JSON Lines.

    A unidade de trabalho é um `(deputado, ano)`. O extrator usa a estratégia
    padronizada do projeto para retomada: arquivo final, `.tmp`, `.empty` e
    `.state.json`.
    """

    def __init__(self, nome_endpoint, configuracao, session=None, proxy=None):
        """Armazena a configuração operacional e dependências opcionais."""

        super().__init__("camara")
        config_extrator = obter_parametros_extrator("camara.deputados_despesas")

        self.nome_endpoint = nome_endpoint
        self.configuracao = configuracao
        self.endpoint = configuracao["endpoint"]
        self.paginacao = configuracao["paginacao"]
        self.session = session
        self.proxy = proxy
        self.rate_limit_per_sec = config_extrator.get("rate_limit_per_sec")
        self.max_rate_per_sec = config_extrator.get("max_rate_per_sec")
        self.required_output_keys = {
            "documento_fornecedor_normalizado",
            "tipo_documento_fornecedor",
            "cnpj_base_fornecedor",
            "orgao_origem",
            "endpoint_origem",
            "id_legislatura",
            "nome_deputado",
            "uri_deputado",
            "sigla_uf_deputado",
            "sigla_partido_deputado",
        }

    def _preparar_parametros(self):
        """Resolve placeholders de data e injeta o tamanho da página."""

        params = self.configuracao.get("params", {})
        params = resolver_parametros_data(params)
        params["itens"] = self.configuracao["itens"]
        return params

    def _fazer_requisicao(self, url, params):
        """Executa a chamada HTTP com limites próprios do endpoint de despesas."""

        return http_client.get(
            url=url,
            params=params,
            session=self.session,
            proxy=self.proxy,
            timeout=(10, 60),
            rate_key=f"CAMARA:{self.nome_endpoint}",
            rate_limit_per_sec=self.rate_limit_per_sec,
            max_rate_per_sec=self.max_rate_per_sec,
        )

    def _caminho_saida(self) -> Path:
        """Resolve o caminho final de saída do deputado no ano informado."""

        ano = self.configuracao.get("contexto_ano")
        id_dep = self.configuracao.get("contexto_id")
        return Path("data") / "despesas_deputados_federais" / str(ano) / f"despesas_{id_dep}.json"

    def _caminho_tmp(self) -> Path:
        """Retorna o temporário do arquivo final da tarefa."""

        return self._caminho_saida().with_suffix(".json.tmp")

    def _caminho_empty(self) -> Path:
        """Retorna o marcador de tarefa vazia."""

        return self._caminho_saida().with_suffix(".json.empty")

    def _caminho_estado(self) -> Path:
        """Retorna o checkpoint da tarefa `(deputado, ano)`."""

        ano = self.configuracao.get("contexto_ano")
        id_dep = self.configuracao.get("contexto_id")
        return (
            Path("data/_estado/camara")
            / f"endpoint={self.nome_endpoint}"
            / f"ano={ano}"
            / f"id={id_dep}.state.json"
        )

    def _estado_inicial(self, url: str, params: dict) -> dict:
        """Retorna o estado inicial da paginação da tarefa."""

        return {
            "page": 1,
            "pages": 0,
            "records": 0,
            "next_url": url,
            "params": params,
        }

    def _arquivo_pronto(self) -> bool:
        """Indica se a saída final já está íntegra no esquema atual."""

        return arquivo_jsonl_tem_chaves(self._caminho_saida(), self.required_output_keys)

    def _enriquecer_registro(self, dado: dict) -> dict:
        """Adiciona o contexto do deputado e as chaves derivadas do fornecedor."""

        ano = self.configuracao.get("contexto_ano")
        id_dep = self.configuracao.get("contexto_id")
        contexto = self.configuracao.get("contexto_deputado", {})
        id_legislatura = contexto.get("id_legislatura") or contexto.get("idLegislatura")
        nome_deputado = contexto.get("nome")
        sigla_uf = contexto.get("siglaUf")
        sigla_partido = contexto.get("siglaPartido")
        uri_deputado = contexto.get("uri")

        dado["id_deputado"] = id_dep
        dado["ano_arquivo"] = ano
        if id_legislatura is not None:
            dado["id_legislatura"] = id_legislatura
        if nome_deputado:
            dado["nome_deputado"] = nome_deputado
        if sigla_uf:
            dado["sigla_uf_deputado"] = sigla_uf
        if sigla_partido:
            dado["sigla_partido_deputado"] = sigla_partido
        if uri_deputado:
            dado["uri_deputado"] = uri_deputado

        documento = normalizar_documento(dado.get("cnpjCpfFornecedor"))
        dado["documento_fornecedor_normalizado"] = documento
        dado["tipo_documento_fornecedor"] = tipo_documento(documento)
        dado["cnpj_base_fornecedor"] = base_cnpj(documento)
        dado["orgao_origem"] = "camara"
        dado["endpoint_origem"] = self.nome_endpoint
        return dado

    def executar(
        self,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Percorre todas as páginas disponíveis e retorna um resumo da extração."""

        url_inicial = f"{self.base_url}{self.endpoint}"
        params_iniciais = self._preparar_parametros()
        caminho_saida = self._caminho_saida()
        caminho_tmp = self._caminho_tmp()
        caminho_empty = self._caminho_empty()
        caminho_estado = self._caminho_estado()
        retrying_from_empty = _from_empty_retry

        if self._arquivo_pronto():
            return {"status": "skipped", "records": 0, "pages": 0}

        if caminho_empty.exists():
            if _allow_empty_retry and self._consumir_retry_empty(
                caminho_empty,
                contexto=f"{self.nome_endpoint}:{caminho_saida}",
            ):
                retrying_from_empty = True
            else:
                return {"status": "skipped_empty", "records": 0, "pages": 0}

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
            return {
                "status": "success",
                "records": int(estado.get("records", 0)),
                "pages": int(estado.get("pages", 0)),
            }

        caminho_tmp.parent.mkdir(parents=True, exist_ok=True)
        modo = "a" if estado["records"] > 0 and caminho_tmp.exists() else "w"
        pagina = int(estado["page"])
        paginas_escritas = int(estado["pages"])
        total_registros = int(estado["records"])
        url = estado["next_url"]
        params = estado.get("params")

        with open(caminho_tmp, modo, encoding="utf-8") as f:
            while url:
                resposta = self._fazer_requisicao(url, params)
                dados = resposta.get("dados", [])

                if not dados:
                    break

                self.logger.info(
                    "Página extraída | deputado=%s | ano=%s | pagina=%s | registros=%s",
                    self.configuracao.get("contexto_id"),
                    self.configuracao.get("contexto_ano"),
                    pagina,
                    len(dados),
                )

                for dado in dados:
                    json.dump(self._enriquecer_registro(dado), f, ensure_ascii=False)
                    f.write("\n")

                f.flush()
                total_registros += len(dados)
                paginas_escritas += 1
                pagina += 1

                if not self.paginacao:
                    url = None
                else:
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
                contexto=f"{self.nome_endpoint}:{caminho_saida}",
            ):
                return self.executar(_allow_empty_retry=False, _from_empty_retry=True)
            if not _from_empty_retry:
                caminho_empty.touch()
            elif caminho_empty.exists():
                caminho_empty.unlink()
            return {"status": "empty", "records": 0, "pages": 0}

        if caminho_empty.exists():
            caminho_empty.unlink()

        caminho_tmp.replace(caminho_saida)
        limpar_artefatos(caminho_estado)
        return {
            "status": "success",
            "records": total_registros,
            "pages": paginas_escritas,
        }
