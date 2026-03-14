"""Fábrica de sessões HTTP reutilizáveis para os extratores."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def criar_sessao():
    """Cria uma `requests.Session` com pool e retry de conexão/leitura.

    O retry do adapter é restrito a falhas de transporte. Retentativas por
    status HTTP são tratadas separadamente em `infra.http.cliente`.
    """

    session = requests.Session()

    retry = Retry(
        total=0,
        connect=3,
        read=3,
        backoff_factor=0.5,
        allowed_methods=frozenset({"GET"}),
    )

    adapter = HTTPAdapter(max_retries=retry, pool_connections=32, pool_maxsize=32)

    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "br-etl/1.0"})

    return session
