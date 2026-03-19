"""Cliente HTTP para o endpoint SPARQL do SIOP."""

from __future__ import annotations

import logging
from threading import local

from infra.http.cliente import http_client
from infra.http.sessao import criar_sessao

logger = logging.getLogger(__name__)

_MEDIA_TYPE_JSON = "application/sparql-results+json"
_NO_PROXY = {"http": None, "https": None}

# Tentativas com fallback de media type — o endpoint SIOP é instável quanto
# ao Accept header e às vezes exige o alias curto "JSON".
_FORMATOS_FALLBACK = [
    {"format": _MEDIA_TYPE_JSON, "output": _MEDIA_TYPE_JSON},
    {"format": "JSON", "output": "JSON"},
]


class SiopClienteSPARQL:
    """Executa consultas SPARQL contra o endpoint do SIOP.

    Responsabilidade única: saber *como* fazer uma requisição HTTP ao
    endpoint — incluindo sessão thread-local, fallback de media type e
    rate limiting — sem conhecer queries, arquivos ou transformações.
    """

    def __init__(
        self,
        base_url: str,
        rate_limit_per_sec: float,
        max_rate_per_sec: float,
    ) -> None:
        self._sparql_url = f"{base_url.rstrip('/')}/sparql/"
        self._rate_limit_per_sec = rate_limit_per_sec
        self._max_rate_per_sec = max_rate_per_sec
        self._local = local()

    # ── sessão thread-local ──────────────────────────────────────────────────

    def _get_session(self):
        """Retorna uma sessão HTTP direta exclusiva da thread atual."""

        if not hasattr(self._local, "session"):
            session = criar_sessao()
            session.trust_env = False
            self._local.session = session
        return self._local.session

    @staticmethod
    def _headers() -> dict:
        return {
            "Accept": f"{_MEDIA_TYPE_JSON}, application/json;q=0.9, */*;q=0.1",
        }



    def fazer_requisicao(
        self,
        query: str,
        ano: int | None = None,
        timeout: tuple[int, int] = (15, 60),
    ) -> dict:
        """Executa a consulta SPARQL com fallback automático de media type.

        Tenta primeiro com o media type padrão; em caso de falha, retenta com
        o alias curto "JSON". Lança a última exceção se todas as tentativas
        falharem.
        """

        ultima_excecao: Exception | None = None

        for indice, fmt in enumerate(_FORMATOS_FALLBACK, start=1):
            params = {"query": query, **fmt}
            try:
                return http_client.get(
                    url=self._sparql_url,
                    params=params,
                    retries=1,
                    headers=self._headers(),
                    session=self._get_session(),
                    proxy=_NO_PROXY,
                    timeout=timeout,
                    rate_key="SIOP",
                    rate_limit_per_sec=self._rate_limit_per_sec,
                    max_rate_per_sec=self._max_rate_per_sec,
                )
            except Exception as exc:
                ultima_excecao = exc
                if indice < len(_FORMATOS_FALLBACK):
                    logger.warning(
                        "[SIOP] Falha na tentativa %s com formato %s | ano=%s | tentando fallback.",
                        indice,
                        fmt["format"],
                        ano,
                    )

        raise ultima_excecao

    # ── sonda de disponibilidade ─────────────────────────────────────────────

    def ano_tem_dados(self, query_probe: str, ano: int) -> bool:
        """Verifica rapidamente se o ano possui ao menos um ItemDespesa."""

        resposta = self.fazer_requisicao(query_probe, ano=ano, timeout=(10, 20))
        return bool(resposta.get("results", {}).get("bindings", []))