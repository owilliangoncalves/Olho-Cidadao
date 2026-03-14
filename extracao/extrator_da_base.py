"""Base comum para extratores HTTP do projeto."""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Any
from typing import Dict
from typing import Optional

from configuracao.endpoint import urls
from configuracao.logger import logger
from configuracao.projeto import obter_configuracao
from infra.http.cliente import http_client

class ExtratorBase(ABC):
    """Classe base que centraliza URL base, logging e acesso HTTP.

    As subclasses herdam um método `_fazer_requisicao` já integrado ao cliente
    HTTP compartilhado do projeto, mantendo política uniforme de retry, logs e
    rate limiting.
    """

    def __init__(self, orgao: str):
        """Inicializa o extrator para um órgão configurado em `etl-config.toml`."""

        try:
            self.base_url = urls[orgao]["base_url"]
            self.orgao = orgao.upper()
            self.logger = logger
            self._empty_retries_consumed: set[str] = set()
            self._empty_retries_lock = Lock()

            self.logger.debug(
                "[%s] Extrator inicializado | Base URL: %s",
                self.orgao,
                self.base_url,
            )

        except KeyError:
            logger.error("Órgão '%s' não encontrado na configuração.", orgao)
            raise

    def _consumir_retry_empty(self, empty_path: Path, *, contexto: str | None = None) -> bool:
        """Autoriza uma revalidação de `.empty` uma única vez por execução."""

        chave = str(empty_path)
        with self._empty_retries_lock:
            if chave in self._empty_retries_consumed:
                return False
            self._empty_retries_consumed.add(chave)

        if empty_path.exists():
            empty_path.unlink()

        self.logger.warning(
            "[%s] Reprocessando tarefa marcada como vazia | alvo=%s",
            self.orgao,
            contexto or empty_path,
        )
        return True

    def _fazer_requisicao(
        self,
        url: str,
        params: Optional[dict] = None,
        delay: float = 0.0,
        headers: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Executa uma requisição GET padronizada para o extrator atual.

        Args:
            url: URL absoluta ou caminho relativo ao `base_url` do órgão.
            params: Parâmetros de query string.
            delay: Pausa opcional aplicada após sucesso.
            headers: Cabeçalhos adicionais para sobrescrever o padrão.

        Returns:
            Corpo JSON convertido para tipos nativos do Python.

        Raises:
            Exception: Propagada do cliente HTTP quando a requisição falha.
        """

        url_completa = url if url.startswith("http") else f"{self.base_url}{url}"

        default_headers = {
            "Accept": "application/json",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip",
        }

        if headers:
            default_headers.update(headers)

        self.logger.debug("[%s] Request -> %s", self.orgao, url_completa)

        if params:
            self.logger.debug("[%s] Params -> %s", self.orgao, params)

        start = time.time()
        http_defaults = obter_configuracao("config.http.default", default={})
        http_orgao = obter_configuracao(
            f"config.http.{self.orgao.lower()}",
            default={},
        )
        rate_limit_per_sec = http_orgao.get(
            "rate_limit_per_sec",
            http_defaults.get("rate_limit_per_sec"),
        )
        max_rate_per_sec = http_orgao.get(
            "max_rate_per_sec",
            http_defaults.get("max_rate_per_sec"),
        )

        try:
            response = http_client.get(
                url=url_completa,
                params=params,
                headers=default_headers,
                rate_key=self.orgao,
                rate_limit_per_sec=rate_limit_per_sec,
                max_rate_per_sec=max_rate_per_sec,
            )

            duration = time.time() - start
            self.logger.debug("[%s] Sucesso | %.2fs", self.orgao, duration)

            if delay > 0:
                time.sleep(delay)

            return response

        except Exception as exc:
            duration = time.time() - start
            self.logger.error(
                "[%s] Falha | %.2fs | URL=%s | erro=%s",
                self.orgao,
                duration,
                url_completa,
                exc,
            )
            raise

    @abstractmethod
    def executar(self):
        """Executa o fluxo principal do extrator concreto."""
