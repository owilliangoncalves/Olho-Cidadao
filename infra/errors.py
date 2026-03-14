"""Exceções de domínio reutilizáveis pela CLI e pelos extratores."""

from __future__ import annotations


class UserInputError(ValueError):
    """Representa erro de entrada do usuário que não merece stack trace.

    A CLI usa esta exceção para diferenciar:

    - erros de uso/configuração, que devem resultar em mensagem objetiva; e
    - erros internos, que ainda merecem log com traceback.
    """

