"""Cliente HTTP compartilhado com retry, rotação de proxy e rate limiting."""

import logging
import random
import time
from email.utils import parsedate_to_datetime
from threading import Lock, local
from urllib.parse import urlparse

import requests

from infra.http.proxies import proxy_manager
from infra.http.sessao import criar_sessao

logger = logging.getLogger("http_client")


class AdaptiveRateLimiter:
    """Controla a cadência de requisições para uma chave lógica de tráfego.

    A taxa efetiva é ajustada dinamicamente: respostas saudáveis recompensam o
    limitador, enquanto falhas e sinais de saturação reduzem a velocidade.
    """

    def __init__(
        self,
        initial_rate: float,
        min_rate: float,
        max_rate: float,
    ):
        """Inicializa o limitador com os limites operacionais permitidos."""

        self.rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.next_allowed_at = 0.0
        self.lock = Lock()

    def acquire(self):
        """Bloqueia até que a próxima requisição esteja permitida."""

        while True:
            with self.lock:
                now = time.monotonic()
                wait = self.next_allowed_at - now
                if wait <= 0:
                    interval = 1 / max(self.rate, self.min_rate)
                    self.next_allowed_at = now + interval
                    return
            time.sleep(wait)

    def reward(self):
        """Aumenta gradualmente a taxa após respostas bem-sucedidas."""

        with self.lock:
            self.rate = min(self.max_rate, self.rate + 0.2)

    def penalize(self, retry_after: float = 0.0, severe: bool = False):
        """Reduz a taxa quando há sinais de instabilidade do serviço."""

        with self.lock:
            if severe:
                self.rate = max(self.min_rate, self.rate / 2)
            else:
                self.rate = max(self.min_rate, self.rate * 0.85)

            if retry_after > 0:
                self.next_allowed_at = max(
                    self.next_allowed_at,
                    time.monotonic() + retry_after,
                )


class HttpClient:
    """Encapsula requisições GET com políticas compartilhadas de robustez."""

    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self):
        """Inicializa o armazenamento thread-local de sessão e limitadores."""

        self._local = local()
        self._limiters = {}
        self._lock = Lock()

    def _get_session(self):
        """Obtém ou cria a sessão HTTP associada à thread atual."""

        if not hasattr(self._local, "session"):
            self._local.session = criar_sessao()
        return self._local.session

    def _get_limiter(
        self,
        rate_key: str,
        rate_limit_per_sec: float,
        min_rate_per_sec: float,
        max_rate_per_sec: float,
    ) -> AdaptiveRateLimiter:
        """Obtém o limitador associado à chave lógica informada."""

        with self._lock:
            limiter = self._limiters.get(rate_key)
            if limiter is None:
                limiter = AdaptiveRateLimiter(
                    initial_rate=rate_limit_per_sec,
                    min_rate=min_rate_per_sec,
                    max_rate=max_rate_per_sec,
                )
                self._limiters[rate_key] = limiter
            return limiter

    def _resolver_rate_key(self, url: str, rate_key: str | None) -> str:
        """Define a chave de rate limit usada para compartilhar a cadência."""

        if rate_key:
            return rate_key
        parsed = urlparse(url)
        return parsed.netloc or "default"

    def _parse_retry_after(self, value: str | None) -> float:
        """Converte `Retry-After` em segundos, quando presente."""

        if not value:
            return 0.0
        if value.isdigit():
            return float(value)
        try:
            retry_at = parsedate_to_datetime(value)
            return max(0.0, retry_at.timestamp() - time.time())
        except (TypeError, ValueError):
            return 0.0

    def _build_backoff(self, attempt: int, retry_after: float) -> float:
        """Calcula o atraso antes da próxima tentativa com jitter leve."""

        if retry_after > 0:
            return retry_after
        return min(30.0, (2**attempt) + random.uniform(0.0, 0.5))

    def _request_json(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        retries=5,
        session=None,
        proxy=None,
        timeout=(10, 60),
        rate_key=None,
        rate_limit_per_sec=4.0,
        min_rate_per_sec=0.5,
        max_rate_per_sec=8.0,
    ):
        """Executa uma requisição HTTP resiliente e retorna o corpo JSON."""

        rate_key = self._resolver_rate_key(url, rate_key)
        limiter = self._get_limiter(
            rate_key,
            rate_limit_per_sec=rate_limit_per_sec,
            min_rate_per_sec=min_rate_per_sec,
            max_rate_per_sec=max_rate_per_sec,
        )
        session = session or self._get_session()

        for attempt in range(retries):
            limiter.acquire()

            proxy_config = proxy if proxy is not None else proxy_manager.get()
            proxy_url = proxy_config["http"] if proxy_config else "direct"
            started_at = time.perf_counter()

            try:
                response = session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=headers,
                    proxies=proxy_config,
                    timeout=timeout,
                )

                latency = time.perf_counter() - started_at
                status_code = response.status_code

                logger.debug(
                    "HTTP %s %.2fs method=%s rate_key=%s proxy=%s",
                    status_code,
                    latency,
                    method,
                    rate_key,
                    proxy_url,
                )

                if status_code in self.RETRYABLE_STATUS_CODES:
                    retry_after = self._parse_retry_after(
                        response.headers.get("Retry-After")
                    )
                    limiter.penalize(retry_after=retry_after, severe=status_code == 429)

                    if proxy_config:
                        proxy_manager.mark_dead(proxy_config["http"])

                    if attempt == retries - 1:
                        response.raise_for_status()

                    time.sleep(self._build_backoff(attempt, retry_after))
                    continue

                response.raise_for_status()
                limiter.reward()
                return response.json()

            except requests.RequestException as exc:
                latency = time.perf_counter() - started_at

                logger.warning(
                    "Erro request %.2fs rate_key=%s proxy=%s erro=%s",
                    latency,
                    rate_key,
                    proxy_url,
                    exc,
                )

                if proxy_config:
                    proxy_manager.mark_dead(proxy_config["http"])

                severe = False
                if isinstance(exc, requests.HTTPError) and exc.response is not None:
                    severe = exc.response.status_code == 429

                limiter.penalize(severe=severe)

                if attempt == retries - 1:
                    raise

                time.sleep(self._build_backoff(attempt, 0.0))

        raise Exception("Falha apos retries")

    def get(
        self,
        url,
        params=None,
        headers=None,
        retries=5,
        session=None,
        proxy=None,
        timeout=(10, 60),
        rate_key=None,
        rate_limit_per_sec=4.0,
        min_rate_per_sec=0.5,
        max_rate_per_sec=8.0,
    ):
        """Executa um GET resiliente e retorna o corpo já desserializado.

        Args:
            url: URL absoluta a ser consultada.
            params: Parâmetros de query string.
            headers: Cabeçalhos adicionais da requisição.
            retries: Número máximo de tentativas da chamada.
            session: Sessão HTTP opcional para reaproveitamento explícito.
            proxy: Configuração de proxy; `None` delega ao `ProxyManager`.
            timeout: Timeout do `requests`.
            rate_key: Identificador lógico da cota compartilhada.
            rate_limit_per_sec: Taxa inicial desejada.
            min_rate_per_sec: Taxa mínima permitida após penalizações.
            max_rate_per_sec: Taxa máxima permitida após recompensas.

        Returns:
            Estrutura JSON já convertida para tipos nativos do Python.

        Raises:
            requests.RequestException: Propagada após esgotar as tentativas.
            Exception: Levantada apenas se o loop terminar sem retorno, o que
                não é esperado no fluxo normal.
        """
        return self._request_json(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            retries=retries,
            session=session,
            proxy=proxy,
            timeout=timeout,
            rate_key=rate_key,
            rate_limit_per_sec=rate_limit_per_sec,
            min_rate_per_sec=min_rate_per_sec,
            max_rate_per_sec=max_rate_per_sec,
        )

    def post(
        self,
        url,
        data=None,
        headers=None,
        retries=5,
        session=None,
        proxy=None,
        timeout=(10, 60),
        rate_key=None,
        rate_limit_per_sec=4.0,
        min_rate_per_sec=0.5,
        max_rate_per_sec=8.0,
    ):
        """Executa um POST resiliente e retorna o corpo já desserializado."""

        return self._request_json(
            method="POST",
            url=url,
            data=data,
            headers=headers,
            retries=retries,
            session=session,
            proxy=proxy,
            timeout=timeout,
            rate_key=rate_key,
            rate_limit_per_sec=rate_limit_per_sec,
            min_rate_per_sec=min_rate_per_sec,
            max_rate_per_sec=max_rate_per_sec,
        )


http_client = HttpClient()
