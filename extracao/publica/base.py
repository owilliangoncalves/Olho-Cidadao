"""Infraestrutura compartilhada para crawlers de APIs públicas auxiliares."""

from __future__ import annotations

import json
from pathlib import Path
from threading import local

from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import derivar_artefatos_tarefa
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from infra.http.cliente import http_client
from infra.http.sessao import criar_sessao
from utils.jsonl import arquivo_jsonl_meta_tem_chaves


class ExtratorAPIPublicaBase(ExtratorBase):
    """Base para APIs públicas com persistência incremental em JSON Lines."""

    def __init__(
        self,
        orgao: str,
        nome_endpoint: str,
        rate_limit_per_sec: float | None = None,
        max_rate_per_sec: float | None = None,
    ):
        """Configura a base URL, sessão direta e limites de tráfego."""

        super().__init__(orgao=orgao)

        defaults = obter_parametros_extrator("publica")
        self.nome_endpoint = nome_endpoint
        self.rate_limit_per_sec = (
            rate_limit_per_sec
            if rate_limit_per_sec is not None
            else defaults.get("rate_limit_per_sec")
        )
        self.max_rate_per_sec = (
            max_rate_per_sec
            if max_rate_per_sec is not None
            else defaults.get("max_rate_per_sec")
        )
        self.no_proxy = {"http": None, "https": None}
        self._local = local()
        self.required_meta_keys = {
            "orgao_origem",
            "nome_endpoint",
            "endpoint",
        }

    def _get_session(self):
        """Retorna uma sessão HTTP exclusiva da thread atual."""

        if not hasattr(self._local, "session"):
            session = criar_sessao()
            session.trust_env = False
            self._local.session = session
        return self._local.session

    def _request_publica(self, endpoint: str, params: dict | None = None, timeout=(15, 120)):
        """Executa uma chamada HTTP direta para uma API pública."""

        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        return http_client.get(
            url=url,
            params=params,
            session=self._get_session(),
            proxy=self.no_proxy,
            timeout=timeout,
            rate_key=f"{self.orgao}:{self.nome_endpoint}",
            rate_limit_per_sec=self.rate_limit_per_sec,
            max_rate_per_sec=self.max_rate_per_sec,
        )

    def _coerce_items(self, resposta, item_keys=("data", "items", "content", "resultado", "results")):
        """Normaliza diferentes formatos de resposta para uma lista de itens."""

        if isinstance(resposta, list):
            return resposta

        if isinstance(resposta, dict):
            for chave in item_keys:
                valor = resposta.get(chave)
                if isinstance(valor, list):
                    return valor

        return []

    def _caminhos_tarefa(self, relative_output_path: Path):
        """Deriva caminhos de saída, estado e vazio para a tarefa."""

        return derivar_artefatos_tarefa(
            relative_output_path,
            state_root=Path("data/_estado/publica"),
        )

    def _output_pronto(self, output_path: Path, extra_meta_keys: set[str] | None = None) -> bool:
        """Indica se o arquivo existente já contém o esquema mínimo esperado."""

        required = set(self.required_meta_keys)
        if extra_meta_keys:
            required.update(extra_meta_keys)
        return arquivo_jsonl_meta_tem_chaves(output_path, required)

    def _carregar_estado(self, state_path: Path, initial_state: dict) -> dict:
        """Lê o estado atual da tarefa, quando existir."""

        return carregar_estado_json(state_path, initial_state)

    def _salvar_estado(self, state_path: Path, state: dict):
        """Persiste o estado corrente da tarefa."""

        salvar_estado_json(state_path, state)

    def _limpar_estado(self, state_path: Path, tmp_path: Path):
        """Remove artefatos intermediários da tarefa."""

        limpar_artefatos(state_path, tmp_path)

    def _build_record(self, item, context: dict, endpoint: str):
        """Empacota o payload com metadados mínimos de rastreabilidade."""

        return {
            "_meta": {
                **context,
                "endpoint": endpoint,
                "orgao_origem": self.orgao.lower(),
                "nome_endpoint": self.nome_endpoint,
            },
            "payload": item,
        }

    def _executar_tarefa_unica(
        self,
        endpoint: str,
        params: dict,
        relative_output_path: Path,
        context: dict,
        item_keys=("data", "items", "content", "resultado", "results"),
        wrap_dict=False,
        extra_meta_keys: set[str] | None = None,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
        _persist_empty_marker: bool = True,
    ):
        """Executa uma consulta não paginada e persiste o resultado."""

        output_path, state_path, tmp_path, empty_path = self._caminhos_tarefa(relative_output_path)
        retrying_from_empty = _from_empty_retry

        if output_path.exists() and output_path.stat().st_size > 0 and self._output_pronto(
            output_path,
            extra_meta_keys=extra_meta_keys,
        ):
            return {"status": "skipped", "records": 0, "path": output_path}

        if empty_path.exists():
            if not _persist_empty_marker:
                empty_path.unlink()
            elif _allow_empty_retry and self._consumir_retry_empty(
                empty_path,
                contexto=f"{self.nome_endpoint}:{relative_output_path}",
            ):
                retrying_from_empty = True
            else:
                return {"status": "skipped_empty", "records": 0, "path": output_path}

        resposta = self._request_publica(endpoint, params=params)
        items = self._coerce_items(resposta, item_keys=item_keys)

        if not items and wrap_dict and isinstance(resposta, dict):
            items = [resposta]

        if not items:
            self._limpar_estado(state_path, tmp_path)
            if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                empty_path,
                contexto=f"{self.nome_endpoint}:{relative_output_path}",
            ):
                return self._executar_tarefa_unica(
                    endpoint=endpoint,
                    params=params,
                    relative_output_path=relative_output_path,
                    context=context,
                    item_keys=item_keys,
                    wrap_dict=wrap_dict,
                    extra_meta_keys=extra_meta_keys,
                    _allow_empty_retry=False,
                    _from_empty_retry=True,
                    _persist_empty_marker=_persist_empty_marker,
                )
            if _persist_empty_marker and not _from_empty_retry:
                empty_path.touch()
            elif empty_path.exists():
                empty_path.unlink()
            return {"status": "empty", "records": 0, "path": output_path}

        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in items:
                json.dump(self._build_record(item, context, endpoint), f, ensure_ascii=False)
                f.write("\n")

        if empty_path.exists():
            empty_path.unlink()
        tmp_path.replace(output_path)
        limpar_artefatos(state_path)

        return {"status": "success", "records": len(items), "path": output_path}

    def _executar_tarefa_paginada(
        self,
        endpoint: str,
        base_params: dict,
        relative_output_path: Path,
        context: dict,
        pagination: dict,
        item_keys=("data", "items", "content", "resultado", "results"),
        extra_meta_keys: set[str] | None = None,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
        _persist_empty_marker: bool = True,
    ):
        """Executa uma tarefa paginada com retomada em arquivo de estado."""

        output_path, state_path, tmp_path, empty_path = self._caminhos_tarefa(relative_output_path)
        retrying_from_empty = _from_empty_retry

        if output_path.exists() and output_path.stat().st_size > 0 and self._output_pronto(
            output_path,
            extra_meta_keys=extra_meta_keys,
        ):
            return {"status": "skipped", "records": 0, "pages": 0, "path": output_path}

        if empty_path.exists():
            if not _persist_empty_marker:
                empty_path.unlink()
            elif _allow_empty_retry and self._consumir_retry_empty(
                empty_path,
                contexto=f"{self.nome_endpoint}:{relative_output_path}",
            ):
                retrying_from_empty = True
            else:
                return {"status": "skipped_empty", "records": 0, "pages": 0, "path": output_path}

        style = pagination["style"]
        initial_state = (
            {"page": pagination.get("start_page", 1), "records": 0, "pages": 0}
            if style == "page"
            else {"offset": pagination.get("start_offset", 0), "records": 0, "pages": 0}
        )
        state = self._carregar_estado(state_path, initial_state)

        if style == "page":
            cursor = state["page"]
            if cursor == pagination.get("start_page", 1) and tmp_path.exists():
                tmp_path.unlink()
        else:
            cursor = state["offset"]
            if cursor == pagination.get("start_offset", 0) and tmp_path.exists():
                tmp_path.unlink()
            if cursor > pagination.get("start_offset", 0) and not tmp_path.exists():
                state = dict(initial_state)
                cursor = state["offset"]

        total_records = state["records"]
        pages_written = state["pages"]
        mode = "a" if total_records > 0 and tmp_path.exists() else "w"

        with open(tmp_path, mode, encoding="utf-8") as f:
            while True:
                params = dict(base_params)
                page_size = pagination.get("page_size")

                if style == "page":
                    params[pagination.get("page_param", "pagina")] = cursor
                    page_size_param = pagination.get("page_size_param")
                    if page_size_param and page_size:
                        params[page_size_param] = page_size
                else:
                    params[pagination.get("offset_param", "offset")] = cursor
                    params[pagination.get("limit_param", "limit")] = page_size

                self.logger.info(
                    "[%s] endpoint=%s cursor=%s contexto=%s",
                    self.orgao,
                    self.nome_endpoint,
                    cursor,
                    context,
                )

                resposta = self._request_publica(endpoint, params=params)
                items = self._coerce_items(resposta, item_keys=item_keys)

                if not items:
                    break

                for item in items:
                    json.dump(self._build_record(item, context, endpoint), f, ensure_ascii=False)
                    f.write("\n")
                    total_records += 1

                f.flush()
                pages_written += 1

                if style == "page":
                    cursor += 1
                    state = {"page": cursor, "records": total_records, "pages": pages_written}
                    page_size_param = pagination.get("page_size_param")
                    if page_size and page_size_param and len(items) < page_size:
                        self._salvar_estado(state_path, state)
                        break
                else:
                    cursor += len(items)
                    state = {"offset": cursor, "records": total_records, "pages": pages_written}
                    if page_size and len(items) < page_size:
                        self._salvar_estado(state_path, state)
                        break

                self._salvar_estado(state_path, state)

        if total_records == 0:
            self._limpar_estado(state_path, tmp_path)
            if not retrying_from_empty and _allow_empty_retry and self._consumir_retry_empty(
                empty_path,
                contexto=f"{self.nome_endpoint}:{relative_output_path}",
            ):
                return self._executar_tarefa_paginada(
                    endpoint=endpoint,
                    base_params=base_params,
                    relative_output_path=relative_output_path,
                    context=context,
                    pagination=pagination,
                    item_keys=item_keys,
                    extra_meta_keys=extra_meta_keys,
                    _allow_empty_retry=False,
                    _from_empty_retry=True,
                    _persist_empty_marker=_persist_empty_marker,
                )
            if _persist_empty_marker and not _from_empty_retry:
                empty_path.touch()
            elif empty_path.exists():
                empty_path.unlink()
            return {"status": "empty", "records": 0, "pages": 0, "path": output_path}

        if empty_path.exists():
            empty_path.unlink()
        tmp_path.replace(output_path)
        limpar_artefatos(state_path)

        return {
            "status": "success",
            "records": total_records,
            "pages": pages_written,
            "path": output_path,
        }
