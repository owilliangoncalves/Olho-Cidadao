"""Extrator do endpoint SPARQL do SIOP para itens de despesa do orçamento."""

from __future__ import annotations

import json
import re
from datetime import datetime
from datetime import timezone
from pathlib import Path
from threading import local
from urllib.parse import urlencode

from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase
from infra.http.cliente import http_client
from infra.http.sessao import criar_sessao
from utils.jsonl import arquivo_jsonl_tem_chaves
from utils.jsonl import contar_registros_jsonl


class ExtratorSIOP(ExtratorBase):
    """Extrai itens de despesa do SIOP com granularidade próxima ao crawler da Câmara.

    O endpoint SPARQL do SIOP é sensível a consultas grandes. Em vez de pedir
    um ano inteiro com todos os joins de uma vez, o crawler trabalha em
    partições menores:

    - ano -> função orçamentária -> página de IDs -> lote pequeno de detalhes;
    - retomada por partição com arquivo de estado;
    - escrita incremental em `.tmp` com promoção atômica ao final;
    - reaproveitamento de partições e arquivos anuais já válidos;
    - sessão HTTP direta, sem proxy, para evitar interferência de rede.
    """

    def __init__(self):
        """Configura caminhos, limites operacionais e sessão HTTP por thread."""

        super().__init__("siop")

        config = obter_parametros_extrator("siop")
        self.caminho_salvo = Path("orcamento_item_despesa")
        self.page_size_inicial = config.get("page_size_inicial")
        self.page_size_minima = config.get("page_size_minima")
        self.detail_batch_size = config.get("detail_batch_size")
        self.max_query_length = config.get("max_query_length")
        self.rate_limit_per_sec = config.get("rate_limit_per_sec")
        self.max_rate_per_sec = config.get("max_rate_per_sec")
        self.funcoes_orcamentarias = tuple(config.get("funcoes_orcamentarias", ()))
        self.estado_dir = Path("data/_estado/siop")
        self.required_output_keys = {
            "uri_item",
            "grafo_orcamentario_uri",
            "uri_funcao",
            "uri_subfuncao",
            "uri_programa",
            "uri_acao",
            "uri_unidade_orcamentaria",
            "codigo_unidade_orcamentaria",
            "uri_fonte",
            "codigo_fonte",
            "uri_gnd",
            "codigo_gnd",
            "uri_modalidade",
            "codigo_modalidade",
            "uri_elemento",
            "codigo_elemento",
            "orgao_origem",
        }
        self._local = local()
        self.no_proxy = {"http": None, "https": None}

    def _agora_iso(self) -> str:
        """Retorna o timestamp atual em UTC para persistência local."""

        return datetime.now(timezone.utc).isoformat()

    def _get_session(self):
        """Retorna uma sessão HTTP direta exclusiva da thread atual."""

        if not hasattr(self._local, "session"):
            session = criar_sessao()
            session.trust_env = False
            self._local.session = session
        return self._local.session

    def _headers_sparql(self) -> dict:
        """Retorna cabeçalhos compatíveis com respostas SPARQL em JSON."""

        return {
            "Accept": "application/sparql-results+json, application/json;q=0.9, */*;q=0.1",
        }

    def _fazer_requisicao_sparql(
        self,
        query: str,
        ano: int | None = None,
        timeout: tuple[int, int] = (15, 60),
    ):
        """Executa uma consulta SPARQL com fallback de media type."""

        tentativas = [
            {
                "query": query,
                "format": "application/sparql-results+json",
                "output": "application/sparql-results+json",
            },
            {
                "query": query,
                "format": "JSON",
                "output": "JSON",
            },
        ]

        ultima_excecao = None

        for indice, params in enumerate(tentativas, start=1):
            try:
                return http_client.get(
                    url=f"{self.base_url.rstrip('/')}/sparql/",
                    params=params,
                    retries=1,
                    headers=self._headers_sparql(),
                    session=self._get_session(),
                    proxy=self.no_proxy,
                    timeout=timeout,
                    rate_key="SIOP",
                    rate_limit_per_sec=self.rate_limit_per_sec,
                    max_rate_per_sec=self.max_rate_per_sec,
                )
            except Exception as exc:
                ultima_excecao = exc
                if indice < len(tentativas):
                    self.logger.warning(
                        "[SIOP] Falha na tentativa %s com formato %s | ano=%s | tentando fallback.",
                        indice,
                        params["format"],
                        ano,
                    )

        raise ultima_excecao

    def _anos_locais(self) -> list[int]:
        """Infere anos já tocados a partir de saídas e checkpoints locais."""

        anos = set()
        padrao = re.compile(r"(?:orcamento_item_despesa_|ano=)(\d{4})")
        diretorios = [
            Path("data") / self.caminho_salvo,
            self.estado_dir,
        ]

        for diretorio in diretorios:
            if not diretorio.exists():
                continue

            for caminho in diretorio.rglob("*"):
                match = padrao.search(str(caminho))
                if match:
                    anos.add(int(match.group(1)))

        return sorted(anos, reverse=True)

    def _anos_priorizados(self) -> list[int]:
        """Monta a fila de anos sem depender de uma discovery global cara."""

        ano_atual = datetime.now().year
        ano_fechado = ano_atual - 1
        fila = [ano_fechado, ano_atual]
        fila.extend(ano for ano in self._anos_locais() if ano not in {ano_fechado, ano_atual})
        fila.extend(range(ano_atual - 2, 2009, -1))

        ordenados = []
        vistos = set()

        for ano in fila:
            if ano < 2010 or ano in vistos:
                continue
            vistos.add(ano)
            ordenados.append(ano)

        return ordenados

    def _query_ano_tem_dados(self, ano: int) -> str:
        """Monta uma sonda leve para verificar se o ano possui itens."""

        return f"""
        PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>

        SELECT ?item
        WHERE {{
          GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
            ?item a loa:ItemDespesa .
          }}
        }}
        LIMIT 1
        """

    def _ano_tem_dados(self, ano: int) -> bool:
        """Verifica rapidamente se o ano possui qualquer item de despesa."""

        resposta = self._fazer_requisicao_sparql(
            self._query_ano_tem_dados(ano),
            ano=ano,
            timeout=(10, 20),
        )
        return bool(resposta.get("results", {}).get("bindings", []))

    def _query_ids_item_despesa(
        self,
        ano: int,
        funcao_codigo: str,
        limit: int,
        last_item_uri: str | None = None,
    ) -> str:
        """Monta a consulta leve que retorna apenas os IDs da página."""

        filtro_cursor = ""
        if last_item_uri:
            filtro_cursor = f'\n            FILTER(STR(?item) > "{last_item_uri}")'

        return f"""
        PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>

        SELECT ?item
        WHERE {{
          GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
            ?item a loa:ItemDespesa .
            ?item loa:temFuncao ?funcao .
            ?funcao loa:codigo "{funcao_codigo}" .
            {filtro_cursor}
          }}
        }}
        ORDER BY ?item
        LIMIT {limit}
        """

    def _query_detalhes_itens(self, ano: int, item_uris: list[str]) -> str:
        """Monta a consulta detalhada para um lote pequeno de itens."""

        itens = ", ".join(f"<{uri}>" for uri in item_uris)
        return f"""
        PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT
          ?item
          ?funcao ?funcao_nome
          ?subfuncao ?subfuncao_nome
          ?programa ?programa_nome
          ?acao ?acao_nome
          ?unidade ?unidade_nome
          ?fonte ?fonte_nome
          ?gnd ?gnd_nome
          ?modalidade ?modalidade_nome
          ?elemento ?elemento_nome
          ?valorPago
          ?valorEmpenhado
          ?valorLiquidado
        WHERE {{
          GRAPH <http://orcamento.dados.gov.br/{ano}/> {{
            ?item a loa:ItemDespesa .
            FILTER(?item IN ({itens})) .

            ?item loa:temFuncao ?funcao .
            ?funcao rdfs:label ?funcao_nome .

            ?item loa:temSubfuncao ?subfuncao .
            ?subfuncao rdfs:label ?subfuncao_nome .

            ?item loa:temPrograma ?programa .
            ?programa rdfs:label ?programa_nome .

            ?item loa:temAcao ?acao .
            ?acao rdfs:label ?acao_nome .

            ?item loa:temUnidadeOrcamentaria ?unidade .
            ?unidade rdfs:label ?unidade_nome .

            ?item loa:temFonteRecursos ?fonte .
            ?fonte rdfs:label ?fonte_nome .

            ?item loa:temGND ?gnd .
            ?gnd rdfs:label ?gnd_nome .

            ?item loa:temModalidadeAplicacao ?modalidade .
            ?modalidade rdfs:label ?modalidade_nome .

            ?item loa:temElementoDespesa ?elemento .
            ?elemento rdfs:label ?elemento_nome .

            ?item loa:valorPago ?valorPago .
            ?item loa:valorEmpenhado ?valorEmpenhado .
            ?item loa:valorLiquidado ?valorLiquidado .
          }}
        }}
        ORDER BY ?item
        """

    def _query_excede_limite_url(self, query: str) -> bool:
        """Indica se a query ultrapassa o limite seguro para GET."""

        estimado = urlencode(
            {
                "query": query,
                "format": "application/sparql-results+json",
                "output": "application/sparql-results+json",
            }
        )
        return len(estimado) > int(self.max_query_length)

    def _binding_value(self, item: dict, chave: str) -> str | None:
        """Extrai o valor textual de um binding SPARQL, quando presente."""

        valor = item.get(chave)
        if not isinstance(valor, dict):
            return None
        return valor.get("value")

    def _codigo_da_uri(self, uri: str | None) -> str | None:
        """Extrai o último segmento significativo de uma URI RDF."""

        if not uri:
            return None
        return uri.rstrip("/").split("/")[-1]

    def _transformar_registro(self, ano: int, item: dict) -> dict:
        """Achata um binding SPARQL no formato de saída do projeto."""

        item_uri = self._binding_value(item, "item")
        funcao_uri = self._binding_value(item, "funcao")
        subfuncao_uri = self._binding_value(item, "subfuncao")
        programa_uri = self._binding_value(item, "programa")
        acao_uri = self._binding_value(item, "acao")
        unidade_uri = self._binding_value(item, "unidade")
        fonte_uri = self._binding_value(item, "fonte")
        gnd_uri = self._binding_value(item, "gnd")
        modalidade_uri = self._binding_value(item, "modalidade")
        elemento_uri = self._binding_value(item, "elemento")

        return {
            "ano": ano,
            "uri_item": item_uri,
            "grafo_orcamentario_uri": f"http://orcamento.dados.gov.br/{ano}/",
            "uri_funcao": funcao_uri,
            "codigo_funcao": self._codigo_da_uri(funcao_uri),
            "funcao": self._binding_value(item, "funcao_nome"),
            "uri_subfuncao": subfuncao_uri,
            "codigo_subfuncao": self._codigo_da_uri(subfuncao_uri),
            "subfuncao": self._binding_value(item, "subfuncao_nome"),
            "uri_programa": programa_uri,
            "codigo_programa": self._codigo_da_uri(programa_uri),
            "programa": self._binding_value(item, "programa_nome"),
            "uri_acao": acao_uri,
            "codigo_acao": self._codigo_da_uri(acao_uri),
            "acao": self._binding_value(item, "acao_nome"),
            "uri_unidade_orcamentaria": unidade_uri,
            "codigo_unidade_orcamentaria": self._codigo_da_uri(unidade_uri),
            "unidade_orcamentaria": self._binding_value(item, "unidade_nome"),
            "uri_fonte": fonte_uri,
            "codigo_fonte": self._codigo_da_uri(fonte_uri),
            "fonte": self._binding_value(item, "fonte_nome"),
            "uri_gnd": gnd_uri,
            "codigo_gnd": self._codigo_da_uri(gnd_uri),
            "gnd": self._binding_value(item, "gnd_nome"),
            "uri_modalidade": modalidade_uri,
            "codigo_modalidade": self._codigo_da_uri(modalidade_uri),
            "modalidade": self._binding_value(item, "modalidade_nome"),
            "uri_elemento": elemento_uri,
            "codigo_elemento": self._codigo_da_uri(elemento_uri),
            "elemento": self._binding_value(item, "elemento_nome"),
            "orgao_origem": "siop",
            "valor_pago": self._binding_value(item, "valorPago"),
            "valor_empenhado": self._binding_value(item, "valorEmpenhado"),
            "valor_liquidado": self._binding_value(item, "valorLiquidado"),
        }

    def _arquivo_saida(self, ano: int) -> Path:
        """Retorna o arquivo final consolidado do ano."""

        return Path("data") / self.caminho_salvo / f"orcamento_item_despesa_{ano}.json"

    def _arquivo_tmp(self, ano: int) -> Path:
        """Retorna o temporário do arquivo consolidado anual."""

        return self._arquivo_saida(ano).with_suffix(".json.tmp")

    def _arquivo_empty(self, ano: int) -> Path:
        """Retorna o marcador de ano vazio."""

        return self._arquivo_saida(ano).with_suffix(".json.empty")

    def _arquivo_pronto(self, ano: int) -> bool:
        """Indica se o arquivo final do ano já está no esquema atual."""

        return arquivo_jsonl_tem_chaves(self._arquivo_saida(ano), self.required_output_keys)

    def _arquivo_saida_particao(self, ano: int, funcao_codigo: str) -> Path:
        """Retorna o arquivo final da partição `ano x função`."""

        return (
            Path("data")
            / self.caminho_salvo
            / "_particoes"
            / f"ano={ano}"
            / f"funcao={funcao_codigo}.json"
        )

    def _arquivo_tmp_particao(self, ano: int, funcao_codigo: str) -> Path:
        """Retorna o arquivo temporário da partição `ano x função`."""

        return self._arquivo_saida_particao(ano, funcao_codigo).with_suffix(".json.tmp")

    def _arquivo_empty_particao(self, ano: int, funcao_codigo: str) -> Path:
        """Retorna o marcador vazio da partição `ano x função`."""

        return self._arquivo_saida_particao(ano, funcao_codigo).with_suffix(".json.empty")

    def _arquivo_estado_particao(self, ano: int, funcao_codigo: str) -> Path:
        """Retorna o arquivo de estado da partição `ano x função`."""

        return (
            self.estado_dir
            / "particoes"
            / f"ano={ano}"
            / f"funcao={funcao_codigo}.state.json"
        )

    def _particao_pronta(self, ano: int, funcao_codigo: str) -> bool:
        """Indica se a partição já possui saída reaproveitável."""

        return arquivo_jsonl_tem_chaves(
            self._arquivo_saida_particao(ano, funcao_codigo),
            self.required_output_keys,
        )

    def _estado_inicial(self) -> dict:
        """Cria a estrutura padrão de estado de uma partição."""

        return {
            "schema_version": 4,
            "status": "pending",
            "attempts": 0,
            "offset": 0,
            "pages": 0,
            "records": 0,
            "page_size": self.page_size_inicial,
            "last_item_uri": None,
            "message": None,
            "updated_at": None,
        }

    def _ultima_uri_item_tmp(self, caminho_tmp: Path) -> str | None:
        """Obtém a última `uri_item` válida gravada no temporário da partição."""

        ultima_uri = None
        with open(caminho_tmp, encoding="utf-8") as arquivo:
            for linha in arquivo:
                if not linha.strip():
                    continue
                try:
                    registro = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                uri_item = registro.get("uri_item")
                if uri_item:
                    ultima_uri = uri_item
        return ultima_uri

    def _carregar_estado_particao(self, ano: int, funcao_codigo: str) -> dict:
        """Lê o estado salvo da partição, aceitando arquivos legados."""

        estado = self._estado_inicial()
        caminho = self._arquivo_estado_particao(ano, funcao_codigo)

        if not caminho.exists():
            return estado

        try:
            with open(caminho, encoding="utf-8") as f:
                carregado = json.load(f)
        except json.JSONDecodeError:
            return estado

        if not isinstance(carregado, dict):
            return estado

        for chave in estado:
            if chave in carregado:
                estado[chave] = carregado[chave]

        return estado

    def _salvar_estado_particao(self, ano: int, funcao_codigo: str, estado: dict):
        """Persiste o estado da partição em disco."""

        caminho = self._arquivo_estado_particao(ano, funcao_codigo)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False)

    def _reconciliar_particao_com_tmp(self, ano: int, funcao_codigo: str, estado: dict) -> dict:
        """Alinha o checkpoint ao conteúdo real do arquivo temporário."""

        caminho_tmp = self._arquivo_tmp_particao(ano, funcao_codigo)

        if not caminho_tmp.exists():
            if estado["status"] == "running":
                estado["status"] = "pending"
            estado["offset"] = 0
            estado["pages"] = 0
            estado["records"] = 0
            estado["last_item_uri"] = None
            return estado

        total_tmp = contar_registros_jsonl(caminho_tmp)
        if total_tmp == 0:
            estado["offset"] = 0
            estado["pages"] = 0
            estado["records"] = 0
            estado["last_item_uri"] = None
            return estado

        ultima_uri_tmp = self._ultima_uri_item_tmp(caminho_tmp)

        if estado["records"] != total_tmp or estado["offset"] < total_tmp:
            self.logger.warning(
                "[SIOP] Reconciliando particao | ano=%s | funcao=%s | "
                "estado=(offset=%s,paginas=%s,registros=%s) | tmp_registros=%s",
                ano,
                funcao_codigo,
                estado["offset"],
                estado["pages"],
                estado["records"],
                total_tmp,
            )
            estado["records"] = total_tmp
            estado["offset"] = max(int(estado.get("offset") or 0), total_tmp)
        if ultima_uri_tmp and estado.get("last_item_uri") != ultima_uri_tmp:
            estado["last_item_uri"] = ultima_uri_tmp

        return estado

    def _marcar_estado_particao_final(
        self,
        ano: int,
        funcao_codigo: str,
        estado: dict,
        status: str,
        message: str | None = None,
    ):
        """Persiste o estado final de uma partição."""

        estado["status"] = status
        estado["message"] = message
        estado["updated_at"] = self._agora_iso()
        self._salvar_estado_particao(ano, funcao_codigo, estado)

    def _buscar_ids_pagina(
        self,
        ano: int,
        funcao_codigo: str,
        last_item_uri: str | None,
        page_size: int,
    ) -> tuple[list[str], int]:
        """Busca os IDs da próxima página com redução adaptativa de carga."""

        tamanho_atual = max(self.page_size_minima, page_size)
        ultima_excecao = None

        while tamanho_atual >= self.page_size_minima:
            try:
                resposta = self._fazer_requisicao_sparql(
                    self._query_ids_item_despesa(
                        ano,
                        funcao_codigo,
                        tamanho_atual,
                        last_item_uri=last_item_uri,
                    ),
                    ano=ano,
                    timeout=(10, 30),
                )
                bindings = resposta.get("results", {}).get("bindings", [])
                item_uris = [
                    item["item"]["value"]
                    for item in bindings
                    if item.get("item", {}).get("value")
                ]
                return item_uris, tamanho_atual
            except Exception as exc:
                ultima_excecao = exc
                response = getattr(exc, "response", None)
                if getattr(response, "status_code", None) == 400:
                    self.logger.error(
                        "[SIOP] Consulta de IDs rejeitada pela API | ano=%s | funcao=%s | offset=%s | page_size=%s",
                        ano,
                        funcao_codigo,
                        last_item_uri or 0,
                        tamanho_atual,
                    )
                    break
                if tamanho_atual == self.page_size_minima:
                    break

                proximo = max(self.page_size_minima, tamanho_atual // 2)
                if proximo == tamanho_atual:
                    break

                self.logger.warning(
                    "[SIOP] Reduzindo page_size de IDs | ano=%s | funcao=%s | offset=%s | de=%s para=%s",
                    ano,
                    funcao_codigo,
                    last_item_uri or 0,
                    tamanho_atual,
                    proximo,
                )
                tamanho_atual = proximo

        raise ultima_excecao

    def _buscar_detalhes_lote(self, ano: int, item_uris: list[str]) -> list[dict]:
        """Busca os detalhes de um lote, dividindo-o quando necessário."""

        if not item_uris:
            return []

        query = self._query_detalhes_itens(ano, item_uris)
        if self._query_excede_limite_url(query):
            if len(item_uris) <= 1:
                raise ValueError(
                    f"Consulta do SIOP excede o limite de URL mesmo com um unico item: {item_uris[0]}"
                )

            meio = len(item_uris) // 2
            esquerda = item_uris[:meio]
            direita = item_uris[meio:]
            self.logger.warning(
                "[SIOP] Dividindo lote preventivamente por limite de URL | ano=%s | itens=%s -> %s + %s",
                ano,
                len(item_uris),
                len(esquerda),
                len(direita),
            )
            return self._buscar_detalhes_lote(ano, esquerda) + self._buscar_detalhes_lote(ano, direita)

        try:
            resposta = self._fazer_requisicao_sparql(
                query,
                ano=ano,
                timeout=(15, 45),
            )
            return resposta.get("results", {}).get("bindings", [])
        except Exception:
            if len(item_uris) <= 1:
                raise

            meio = len(item_uris) // 2
            esquerda = item_uris[:meio]
            direita = item_uris[meio:]
            self.logger.warning(
                "[SIOP] Dividindo lote de detalhes | ano=%s | itens=%s -> %s + %s",
                ano,
                len(item_uris),
                len(esquerda),
                len(direita),
            )
            return self._buscar_detalhes_lote(ano, esquerda) + self._buscar_detalhes_lote(ano, direita)

    def _coletar_registros_detalhados(self, ano: int, item_uris: list[str]) -> list[dict]:
        """Converte URIs de item em registros completos."""

        detalhes_por_uri = {}

        for inicio in range(0, len(item_uris), self.detail_batch_size):
            lote = item_uris[inicio : inicio + self.detail_batch_size]
            bindings = self._buscar_detalhes_lote(ano, lote)

            for item in bindings:
                uri_item = self._binding_value(item, "item")
                if uri_item and uri_item not in detalhes_por_uri:
                    detalhes_por_uri[uri_item] = item

        registros = []
        faltantes = 0

        for uri_item in item_uris:
            binding = detalhes_por_uri.get(uri_item)
            if binding is None:
                faltantes += 1
                binding = {"item": {"value": uri_item}}
            registros.append(self._transformar_registro(ano, binding))

        if faltantes:
            self.logger.warning(
                "[SIOP] Itens sem enriquecimento completo | ano=%s | faltantes=%s",
                ano,
                faltantes,
            )

        return registros

    def _extrair_particao(
        self,
        ano: int,
        funcao_codigo: str,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ) -> dict:
        """Extrai uma partição `ano x função` com retomada local."""

        caminho_saida = self._arquivo_saida_particao(ano, funcao_codigo)
        caminho_tmp = self._arquivo_tmp_particao(ano, funcao_codigo)
        caminho_empty = self._arquivo_empty_particao(ano, funcao_codigo)
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        retrying_from_empty = _from_empty_retry

        if self._particao_pronta(ano, funcao_codigo):
            if caminho_empty.exists():
                caminho_empty.unlink()
            self.logger.info(
                "[SIOP] Particao ja existe, pulando | ano=%s | funcao=%s",
                ano,
                funcao_codigo,
            )
            return {"status": "skipped", "records": 0, "pages": 0}

        if caminho_empty.exists() and not (
            _allow_empty_retry
            and self._consumir_retry_empty(
                caminho_empty,
                contexto=f"siop:ano={ano}:funcao={funcao_codigo}",
            )
        ):
            self.logger.info(
                "[SIOP] Particao vazia ja confirmada, pulando | ano=%s | funcao=%s",
                ano,
                funcao_codigo,
            )
            return {"status": "skipped_empty", "records": 0, "pages": 0}
        elif caminho_empty.exists():
            retrying_from_empty = True

        estado = self._carregar_estado_particao(ano, funcao_codigo)
        estado = self._reconciliar_particao_com_tmp(ano, funcao_codigo, estado)

        if estado["records"] == 0 and caminho_tmp.exists():
            caminho_tmp.unlink()

        estado["status"] = "running"
        estado["attempts"] = int(estado.get("attempts") or 0) + 1
        estado["message"] = None
        estado["updated_at"] = self._agora_iso()
        self._salvar_estado_particao(ano, funcao_codigo, estado)

        modo = "a" if estado["records"] > 0 and caminho_tmp.exists() else "w"

        try:
            with open(caminho_tmp, modo, encoding="utf-8") as f:
                while True:
                    self.logger.info(
                        "[SIOP] Ano %s | funcao=%s | offset=%s | paginas=%s | registros=%s | page_size=%s",
                        ano,
                        funcao_codigo,
                        estado["offset"],
                        estado["pages"],
                        estado["records"],
                        estado["page_size"],
                    )

                    item_uris, page_size_efetivo = self._buscar_ids_pagina(
                        ano,
                        funcao_codigo,
                        estado.get("last_item_uri"),
                        int(estado["page_size"]),
                    )
                    estado["page_size"] = page_size_efetivo

                    if not item_uris:
                        break

                    registros = self._coletar_registros_detalhados(ano, item_uris)
                    for registro in registros:
                        json.dump(registro, f, ensure_ascii=False)
                        f.write("\n")

                    f.flush()
                    estado["records"] += len(registros)
                    estado["pages"] += 1
                    estado["offset"] += len(item_uris)
                    estado["last_item_uri"] = item_uris[-1]
                    estado["updated_at"] = self._agora_iso()
                    self._salvar_estado_particao(ano, funcao_codigo, estado)

                    if len(item_uris) < page_size_efetivo:
                        break

            if estado["records"] == 0:
                if caminho_tmp.exists():
                    caminho_tmp.unlink()
                if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                    caminho_empty,
                    contexto=f"siop:ano={ano}:funcao={funcao_codigo}",
                ):
                    return self._extrair_particao(
                        ano,
                        funcao_codigo,
                        _allow_empty_retry=False,
                        _from_empty_retry=True,
                    )
                if not _from_empty_retry:
                    caminho_empty.touch()
                elif caminho_empty.exists():
                    caminho_empty.unlink()
                self._marcar_estado_particao_final(
                    ano,
                    funcao_codigo,
                    estado,
                    status="empty",
                    message="particao sem registros",
                )
                return {"status": "empty", "records": 0, "pages": 0}

            caminho_tmp.replace(caminho_saida)
            if caminho_empty.exists():
                caminho_empty.unlink()
            self._marcar_estado_particao_final(ano, funcao_codigo, estado, status="success")
            return {
                "status": "success",
                "records": estado["records"],
                "pages": estado["pages"],
            }
        except Exception as exc:
            self._marcar_estado_particao_final(
                ano,
                funcao_codigo,
                estado,
                status="error",
                message=str(exc)[:1000],
            )
            raise

    def _mesclar_particoes_ano(self, ano: int) -> dict:
        """Monta o arquivo anual final a partir das partições concluídas."""

        caminho_final = self._arquivo_saida(ano)
        caminho_tmp = self._arquivo_tmp(ano)
        caminho_empty = self._arquivo_empty(ano)

        if caminho_tmp.exists():
            caminho_tmp.unlink()

        total_registros = 0
        with open(caminho_tmp, "w", encoding="utf-8") as destino:
            for funcao_codigo in self.funcoes_orcamentarias:
                caminho_particao = self._arquivo_saida_particao(ano, funcao_codigo)
                if not caminho_particao.exists():
                    continue

                with open(caminho_particao, encoding="utf-8") as origem:
                    for linha in origem:
                        if not linha.strip():
                            continue
                        destino.write(linha)
                        total_registros += 1

        if total_registros == 0:
            if caminho_tmp.exists():
                caminho_tmp.unlink()
            caminho_empty.touch()
            self.logger.warning("[SIOP] Ano %s consolidado como vazio.", ano)
            return {"status": "empty", "records": 0, "pages": 0}

        caminho_tmp.replace(caminho_final)
        if caminho_empty.exists():
            caminho_empty.unlink()
        self.logger.info(
            "[SIOP] Ano %s consolidado | registros=%s | arquivo=%s",
            ano,
            total_registros,
            caminho_final,
        )
        return {"status": "success", "records": total_registros, "pages": 0}

    def _extrair_ano(
        self,
        ano: int,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ) -> dict:
        """Extrai todas as partições de um ano e consolida o arquivo final."""

        self._arquivo_saida(ano).parent.mkdir(parents=True, exist_ok=True)
        retrying_from_empty = _from_empty_retry

        if self._arquivo_pronto(ano):
            self.logger.info("[SIOP] Ano %s ja existe, pulando.", ano)
            return {"status": "skipped", "records": 0, "pages": 0}

        if self._arquivo_empty(ano).exists() and not (
            _allow_empty_retry
            and self._consumir_retry_empty(
                self._arquivo_empty(ano),
                contexto=f"siop:ano={ano}",
            )
        ):
            self.logger.info("[SIOP] Ano %s ja foi marcado como vazio, pulando.", ano)
            return {"status": "skipped_empty", "records": 0, "pages": 0}
        elif self._arquivo_empty(ano).exists():
            retrying_from_empty = True

        try:
            if not self._ano_tem_dados(ano):
                if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                    self._arquivo_empty(ano),
                    contexto=f"siop:ano={ano}",
                ):
                    return self._extrair_ano(
                        ano,
                        _allow_empty_retry=False,
                        _from_empty_retry=True,
                    )
                if not _from_empty_retry:
                    self._arquivo_empty(ano).touch()
                elif self._arquivo_empty(ano).exists():
                    self._arquivo_empty(ano).unlink()
                self.logger.info("[SIOP] Ano %s sem dados no probe leve, pulando particoes.", ano)
                return {"status": "empty", "records": 0, "pages": 0}
        except Exception as exc:
            self.logger.warning(
                "[SIOP] Probe leve falhou para o ano %s (%s). Seguindo para as particoes.",
                ano,
                exc,
            )

        for funcao_codigo in self.funcoes_orcamentarias:
            self._extrair_particao(ano, funcao_codigo)

        return self._mesclar_particoes_ano(ano)

    def executar(self):
        """Executa a extração do SIOP priorizando os anos mais úteis primeiro."""

        anos = self._anos_priorizados()
        self.logger.info("[SIOP] Iniciando extracao do endpoint SPARQL.")
        self.logger.info("[SIOP] Anos priorizados para extracao: %s", anos)

        if not anos:
            self.logger.warning("[SIOP] Nenhum ano disponivel foi encontrado.")
            return

        stats = {
            "completed": 0,
            "skipped": 0,
            "empty": 0,
            "failed": 0,
        }

        for ano in anos:
            try:
                resumo = self._extrair_ano(ano)
            except Exception:
                stats["failed"] += 1
                self.logger.exception("[SIOP] Falha critica no ano %s", ano)
                continue

            status = resumo["status"]
            if status == "success":
                stats["completed"] += 1
            elif status in {"skipped", "skipped_empty"}:
                stats["skipped"] += 1
            elif status == "empty":
                stats["empty"] += 1

        self.logger.info(
            "[SIOP] Extracao concluida | concluidos=%s | pulados=%s | vazios=%s | falhas=%s",
            stats["completed"],
            stats["skipped"],
            stats["empty"],
            stats["failed"],
        )
