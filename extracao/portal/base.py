"""Infraestrutura comum para extratores do Portal da Transparência."""

import json
import os
from datetime import datetime
from pathlib import Path
from threading import local
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from configuracao.projeto import obter_parametros_extrator
from extracao.extrator_da_base import ExtratorBase
from infra.errors import UserInputError
from infra.estado.arquivos import carregar_estado_json
from infra.estado.arquivos import derivar_artefatos_tarefa
from infra.estado.arquivos import limpar_artefatos
from infra.estado.arquivos import salvar_estado_json
from infra.http.cliente import http_client
from infra.http.sessao import criar_sessao
from utils.documentos import base_cnpj
from utils.documentos import tipo_documento
from utils.jsonl import arquivo_jsonl_meta_tem_chaves

load_dotenv()


class ExtratorPortalBase(ExtratorBase):
    """Base com autenticação, limites oficiais e persistência incremental.

    A API do Portal da Transparência possui cotas diferentes por faixa horária
    e para endpoints restritos. Esta classe encapsula essa regra e oferece uma
    rotina padrão para tarefas paginadas com retomada em arquivo de estado.
    """

    def __init__(self, nome_endpoint: str, restricted: bool = False):
        """Inicializa a sessão direta e valida a presença da chave da API."""

        super().__init__("portal_transparencia")

        api_config = obter_parametros_extrator("portal.api")
        self.nome_endpoint = nome_endpoint
        self.restricted = restricted
        self._local = local()
        self.no_proxy = {"http": None, "https": None}
        self.restricted_limit_rpm = api_config.get("restricted_limit_rpm")
        self.day_limit_rpm = api_config.get("day_limit_rpm")
        self.night_limit_rpm = api_config.get("night_limit_rpm")
        self.default_timezone = api_config.get("timezone")
        self.api_key = (
            os.getenv("PORTAL_TRANSPARENCIA_API_KEY")
            or os.getenv("CHAVE_API_DADOS")
        )
        self.required_meta_keys = {
            "orgao_origem",
            "nome_endpoint",
            "tipo_documento",
            "cnpj_base",
            "endpoint",
        }

        if not self.api_key:
            raise UserInputError(
                "Defina PORTAL_TRANSPARENCIA_API_KEY ou CHAVE_API_DADOS para usar "
                "a API do Portal da Transparencia."
            )

    def _get_session(self):
        """Retorna uma sessão HTTP direta exclusiva da thread atual."""

        if not hasattr(self._local, "session"):
            session = criar_sessao()
            session.trust_env = False
            self._local.session = session
        return self._local.session

    def _headers_portal(self) -> dict:
        """Retorna os cabeçalhos exigidos pela API do Portal."""

        return {
            "Accept": "application/json",
            "chave-api-dados": self.api_key,
        }

    def _limite_rpm_atual(self) -> int:
        """Calcula o limite oficial aplicável ao horário atual."""

        if self.restricted:
            return self.restricted_limit_rpm

        agora = datetime.now(ZoneInfo(self.default_timezone))
        if 0 <= agora.hour < 6:
            return self.night_limit_rpm
        return self.day_limit_rpm

    def _rate_per_sec(self) -> float:
        """Converte o limite em RPM para uma taxa segura por segundo."""

        return max(0.5, (self._limite_rpm_atual() / 60.0) * 0.9)

    def _request_portal(self, endpoint: str, params: dict):
        """Executa uma chamada autenticada ao Portal da Transparência."""

        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        rate_per_sec = self._rate_per_sec()
        limite_rpm = self._limite_rpm_atual()

        return http_client.get(
            url=url,
            params=params,
            headers=self._headers_portal(),
            session=self._get_session(),
            proxy=self.no_proxy,
            timeout=(15, 120),
            rate_key=f"PORTAL:{self.nome_endpoint}:{limite_rpm}",
            rate_limit_per_sec=rate_per_sec,
            max_rate_per_sec=rate_per_sec,
        )

    def _coerce_items(self, resposta):
        """Normaliza formatos de resposta distintos para uma lista de itens."""

        if isinstance(resposta, list):
            return resposta
        if isinstance(resposta, dict):
            for chave in ("data", "dados", "items", "resultado"):
                valor = resposta.get(chave)
                if isinstance(valor, list):
                    return valor
        return []

    def _caminhos_tarefa(self, relative_output_path: Path):
        """Deriva caminhos final, temporário, vazio e de estado da tarefa."""

        return derivar_artefatos_tarefa(
            relative_output_path,
            state_root=Path("data/_estado/portal"),
        )

    def _carregar_estado(self, state_path: Path) -> dict:
        """Lê o estado atual de paginação da tarefa."""

        return carregar_estado_json(state_path, {"page": 1, "records": 0})

    def _salvar_estado(self, state_path: Path, page: int, records: int):
        """Persiste o avanço de paginação da tarefa atual."""

        salvar_estado_json(
            state_path,
            {
                "page": page,
                "records": records,
            },
        )

    def _limpar_estado(self, state_path: Path, tmp_path: Path):
        """Remove artefatos intermediários após sucesso ou vazio definitivo."""

        limpar_artefatos(state_path, tmp_path)

    def _executar_tarefa_paginada(
        self,
        endpoint: str,
        base_params: dict,
        relative_output_path: Path,
        context: dict,
        _allow_empty_retry: bool = True,
        _from_empty_retry: bool = False,
    ):
        """Executa uma tarefa paginada com retomada em arquivo de estado.

        Cada registro é salvo em JSON Lines, embrulhado em um envelope com
        metadados mínimos para rastrear a origem da consulta.
        """

        output_path, state_path, tmp_path, empty_path = self._caminhos_tarefa(relative_output_path)
        documento_contexto = context.get("documento")
        output_join_ready = arquivo_jsonl_meta_tem_chaves(output_path, self.required_meta_keys)
        retrying_from_empty = _from_empty_retry

        if output_path.exists() and output_path.stat().st_size > 0 and output_join_ready:
            return {"status": "skipped", "records": 0, "pages": 0, "path": output_path}

        if empty_path.exists():
            if _allow_empty_retry and self._consumir_retry_empty(
                empty_path,
                contexto=f"{self.nome_endpoint}:{relative_output_path}",
            ):
                retrying_from_empty = True
            else:
                return {"status": "skipped_empty", "records": 0, "pages": 0, "path": output_path}

        state = self._carregar_estado(state_path)
        if state["page"] > 1 and not tmp_path.exists():
            state = {"page": 1, "records": 0}

        if state["page"] == 1 and tmp_path.exists():
            tmp_path.unlink()

        page = state["page"]
        total_records = state["records"]
        mode = "a" if page > 1 and tmp_path.exists() else "w"
        pages_written = max(0, page - 1)

        with open(tmp_path, mode, encoding="utf-8") as f:
            while True:
                params = dict(base_params)
                params["pagina"] = page

                self.logger.info(
                    "[PORTAL] endpoint=%s pagina=%s contexto=%s",
                    self.nome_endpoint,
                    page,
                    context,
                )

                resposta = self._request_portal(endpoint, params)
                items = self._coerce_items(resposta)

                if not items:
                    break

                for item in items:
                    registro = {
                        "_meta": {
                            **context,
                            "pagina": page,
                            "endpoint": endpoint,
                            "orgao_origem": "portal_transparencia",
                            "nome_endpoint": self.nome_endpoint,
                            "tipo_documento": tipo_documento(documento_contexto),
                            "cnpj_base": base_cnpj(documento_contexto),
                        },
                        "payload": item,
                    }
                    json.dump(registro, f, ensure_ascii=False)
                    f.write("\n")
                    total_records += 1

                f.flush()
                pages_written += 1
                page += 1
                self._salvar_estado(state_path, page, total_records)

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
                    _allow_empty_retry=False,
                    _from_empty_retry=True,
                )
            if not _from_empty_retry:
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
