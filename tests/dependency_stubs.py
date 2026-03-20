"""Stubs minimos para dependencias opcionais usadas pelos testes."""

from __future__ import annotations

import sys
import types


def _instalar_stub_requests() -> None:
    if "requests" in sys.modules:
        return

    requests = types.ModuleType("requests")
    adapters = types.ModuleType("requests.adapters")

    class RequestException(Exception):
        pass

    class HTTPError(RequestException):
        def __init__(self, response=None):
            super().__init__("http error")
            self.response = response

    class Session:
        def __init__(self):
            self.headers = {}
            self.trust_env = True

        def mount(self, *_args, **_kwargs):
            return None

        def request(self, *_args, **_kwargs):
            raise NotImplementedError

    class HTTPAdapter:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    requests.RequestException = RequestException
    requests.HTTPError = HTTPError
    requests.Session = Session
    adapters.HTTPAdapter = HTTPAdapter

    sys.modules["requests"] = requests
    sys.modules["requests.adapters"] = adapters


def _instalar_stub_dotenv() -> None:
    if "dotenv" in sys.modules:
        return

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv


def _instalar_stub_urllib3() -> None:
    if "urllib3.util.retry" in sys.modules:
        return

    urllib3 = types.ModuleType("urllib3")
    urllib3_util = types.ModuleType("urllib3.util")
    urllib3_retry = types.ModuleType("urllib3.util.retry")

    class Retry:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    urllib3_retry.Retry = Retry

    sys.modules["urllib3"] = urllib3
    sys.modules["urllib3.util"] = urllib3_util
    sys.modules["urllib3.util.retry"] = urllib3_retry


def install_optional_http_stubs() -> None:
    """Instala stubs locais quando dependencias HTTP nao estao disponiveis."""

    try:
        import requests  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        _instalar_stub_requests()

    try:
        import dotenv  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        _instalar_stub_dotenv()

    try:
        from urllib3.util.retry import Retry  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        _instalar_stub_urllib3()
