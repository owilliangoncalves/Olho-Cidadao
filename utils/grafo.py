"""Utilitários para derivar relações de dependência entre endpoints."""


def construir_grafo(endpoints: dict):
    """Monta um grafo simples de dependências a partir da configuração.

    Cada chave do dicionário resultante representa um endpoint pai e aponta
    para a lista de endpoints que dependem dele.
    """

    grafo = {nome: [] for nome in endpoints}

    for nome, config in endpoints.items():
        depende = config.get("depende_de")
        if depende:
            grafo[depende].append(nome)

    return grafo


def ordem_execucao(endpoints: dict):
    """Calcula uma ordem de execução compatível com as dependências."""

    visitado = set()
    ordem = []

    def dfs(no):
        if no in visitado:
            return

        visitado.add(no)

        depende = endpoints[no].get("depende_de")
        if depende:
            dfs(depende)

        ordem.append(no)

    for no in endpoints:
        dfs(no)

    return ordem
