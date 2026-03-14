"""Resolve placeholders de data usados na configuração de endpoints."""

from datetime import datetime, timedelta


def resolver_parametros_data(params: dict) -> dict:
    """Substitui expressões relativas por datas absolutas.

    Os formatos aceitos hoje são:

    - `hoje`
    - `hoje-<n>d`

    Args:
        params: Dicionário de parâmetros originais.

    Returns:
        Novo dicionário com os valores de data resolvidos.
    """

    hoje = datetime.today()
    resolvidos = {}

    for chave, valor in params.items():
        if valor == "hoje":
            resolvidos[chave] = hoje.strftime("%Y-%m-%d")

        elif (
            isinstance(valor, str) and valor.startswith("hoje-") and valor.endswith("d")
        ):
            dias = int(valor.replace("hoje-", "").replace("d", ""))
            data = hoje - timedelta(days=dias)
            resolvidos[chave] = data.strftime("%Y-%m-%d")

        else:
            resolvidos[chave] = valor

    return resolvidos
