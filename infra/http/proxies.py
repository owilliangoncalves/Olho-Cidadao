"""Gerenciamento simples de rotação de proxies configurados por ambiente."""

import logging
import os
import random
import time
from threading import Lock

from dotenv import load_dotenv

load_dotenv()

RAW_PROXIES = os.getenv("PROXIES", "").split(",")
logger = logging.getLogger("proxy_manager")


def format_proxy(raw):
    """Converte `ip:porta:usuario:senha` no formato aceito pelo `requests`."""

    ip, port, user, pwd = raw.split(":")
    return f"http://{user}:{pwd}@{ip}:{port}"


class ProxyManager:
    """Mantém uma lista rotativa de proxies com janela de cooldown.

    Proxies que falham são marcados temporariamente como indisponíveis para
    reduzir repetição de erros no mesmo nó de saída.
    """

    def __init__(self):
        """Carrega os proxies declarados em `PROXIES` e inicializa o estado."""

        self.proxies = []
        for raw in RAW_PROXIES:
            raw = raw.strip()
            if not raw:
                continue
            try:
                self.proxies.append(format_proxy(raw))
            except ValueError:
                logger.warning("Proxy ignorado por formato invalido: %s", raw)

        self.dead = {}
        self.cooldown = 300
        self.lock = Lock()

    def get(self):
        """Retorna um proxy elegível no formato esperado pelo `requests`."""

        if not self.proxies:
            return None

        with self.lock:
            alive = [
                p
                for p in self.proxies
                if p not in self.dead or time.time() - self.dead[p] > self.cooldown
            ]

            if not alive:
                self.dead = {}
                alive = self.proxies

            proxy = random.choice(alive)

        return {"http": proxy, "https": proxy}

    def mark_dead(self, proxy):
        """Marca um proxy como temporariamente indisponível."""

        if not proxy:
            return
        with self.lock:
            self.dead[proxy] = time.time()


proxy_manager = ProxyManager()
