"""Pacote publica com fachada publica e orquestracao da base compartilhada."""

from __future__ import annotations

from functools import cache
from typing import Any


@cache
def _construir_base_publica():
    """Cria e memoriza a classe base publica do projeto."""

    from pathlib import Path
    from threading import local

    from extracao.extrator_da_base import ExtratorBase
    from extracao.publica.artefatos import derivar_artefatos_publicos
    from extracao.publica.artefatos import output_pronto
    from extracao.publica.config import PublicaBaseConfig
    from extracao.publica.records import DEFAULT_ITEM_KEYS
    from extracao.publica.records import build_record
    from extracao.publica.records import coerce_items
    from extracao.publica.records import write_jsonl_records
    from infra.estado.arquivos import carregar_estado_json
    from infra.estado.arquivos import limpar_artefatos
    from infra.estado.arquivos import salvar_estado_json
    from infra.http.cliente import http_client
    from infra.http.sessao import criar_sessao

    class ExtratorAPIPublicaBase(ExtratorBase):
        """Base para APIs publicas com persistencia incremental em JSON Lines."""

        def __init__(
            self,
            orgao: str,
            nome_endpoint: str,
            rate_limit_per_sec: float | None = None,
            max_rate_per_sec: float | None = None,
        ):
            """Configura a base URL, sessao direta e limites de trafego."""

            super().__init__(orgao=orgao)
            self.publica_cfg = PublicaBaseConfig.carregar(
                rate_limit_per_sec=rate_limit_per_sec,
                max_rate_per_sec=max_rate_per_sec,
            )
            self.nome_endpoint = nome_endpoint
            self.no_proxy = {"http": None, "https": None}
            self._local = local()
            self.required_meta_keys = {
                "orgao_origem",
                "nome_endpoint",
                "endpoint",
            }

        def _get_session(self):
            """Retorna uma sessao HTTP exclusiva da thread atual."""

            if not hasattr(self._local, "session"):
                session = criar_sessao()
                session.trust_env = False
                self._local.session = session
            return self._local.session

        def _request_publica(
            self,
            endpoint: str,
            params: dict | None = None,
            timeout=(15, 120),
        ):
            """Executa uma chamada HTTP direta para uma API publica."""

            endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            return http_client.get(
                url=url,
                params=params,
                session=self._get_session(),
                proxy=self.no_proxy,
                timeout=timeout,
                rate_key=f"{self.orgao}:{self.nome_endpoint}",
                rate_limit_per_sec=self.publica_cfg.rate_limit_per_sec,
                max_rate_per_sec=self.publica_cfg.max_rate_per_sec,
            )

        def _executar_tarefa_unica(
            self,
            endpoint: str,
            params: dict,
            relative_output_path: Path,
            context: dict,
            item_keys=DEFAULT_ITEM_KEYS,
            wrap_dict: bool = False,
            extra_meta_keys: set[str] | None = None,
            _allow_empty_retry: bool = True,
            _from_empty_retry: bool = False,
            _persist_empty_marker: bool = True,
        ):
            """Executa uma consulta nao paginada e persiste o resultado."""

            artifacts = derivar_artefatos_publicos(relative_output_path)
            output_path = artifacts.output_path
            state_path = artifacts.state_path
            tmp_path = artifacts.tmp_path
            empty_path = artifacts.empty_path
            retrying_from_empty = _from_empty_retry

            if output_path.exists() and output_path.stat().st_size > 0 and output_pronto(
                output_path,
                required_meta_keys=self.required_meta_keys,
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
            items = coerce_items(resposta, item_keys=item_keys)
            if not items and wrap_dict and isinstance(resposta, dict):
                items = [resposta]

            if not items:
                limpar_artefatos(state_path, tmp_path)
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

            def build_record_fn(item):
                return build_record(
                    item,
                    context=context,
                    endpoint=endpoint,
                    orgao=self.orgao,
                    nome_endpoint=self.nome_endpoint,
                )

            with open(tmp_path, "w", encoding="utf-8") as handle:
                total = write_jsonl_records(
                    handle,
                    items,
                    build_record_fn=build_record_fn,
                )

            if empty_path.exists():
                empty_path.unlink()
            tmp_path.replace(output_path)
            limpar_artefatos(state_path)

            return {"status": "success", "records": total, "path": output_path}

        def _executar_tarefa_paginada(
            self,
            endpoint: str,
            base_params: dict,
            relative_output_path: Path,
            context: dict,
            pagination: dict,
            item_keys=DEFAULT_ITEM_KEYS,
            extra_meta_keys: set[str] | None = None,
            _allow_empty_retry: bool = True,
            _from_empty_retry: bool = False,
            _persist_empty_marker: bool = True,
        ):
            """Executa uma tarefa paginada com retomada em arquivo de estado."""

            artifacts = derivar_artefatos_publicos(relative_output_path)
            output_path = artifacts.output_path
            state_path = artifacts.state_path
            tmp_path = artifacts.tmp_path
            empty_path = artifacts.empty_path
            retrying_from_empty = _from_empty_retry

            if output_path.exists() and output_path.stat().st_size > 0 and output_pronto(
                output_path,
                required_meta_keys=self.required_meta_keys,
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
            state = carregar_estado_json(state_path, initial_state)

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

            def build_record_fn(item):
                return build_record(
                    item,
                    context=context,
                    endpoint=endpoint,
                    orgao=self.orgao,
                    nome_endpoint=self.nome_endpoint,
                )

            with open(tmp_path, mode, encoding="utf-8") as handle:
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
                    items = coerce_items(resposta, item_keys=item_keys)
                    if not items:
                        break

                    total_records += write_jsonl_records(
                        handle,
                        items,
                        build_record_fn=build_record_fn,
                    )
                    handle.flush()
                    pages_written += 1

                    if style == "page":
                        cursor += 1
                        state = {"page": cursor, "records": total_records, "pages": pages_written}
                        page_size_param = pagination.get("page_size_param")
                        if page_size and page_size_param and len(items) < page_size:
                            salvar_estado_json(state_path, state)
                            break
                    else:
                        cursor += len(items)
                        state = {"offset": cursor, "records": total_records, "pages": pages_written}
                        if page_size and len(items) < page_size:
                            salvar_estado_json(state_path, state)
                            break

                    salvar_estado_json(state_path, state)

            if total_records == 0:
                limpar_artefatos(state_path, tmp_path)
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

    ExtratorAPIPublicaBase.__module__ = __name__
    return ExtratorAPIPublicaBase


def __getattr__(name: str) -> Any:
    """Resolve exports pesados sob demanda."""

    if name == "ExtratorAPIPublicaBase":
        base_publica = _construir_base_publica()
        globals()[name] = base_publica
        return base_publica
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Mantem introspeccao consistente com exports lazy."""

    return sorted(set(globals()) | set(__all__))


__all__ = ["ExtratorAPIPublicaBase"]
