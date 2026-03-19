"""Transformação de bindings SPARQL em registros de domínio do SIOP."""

from __future__ import annotations


class SiopTransformador:
    """Converte um binding SPARQL no formato de saída do projeto.

    Responsabilidade única: saber *como mapear* o resultado bruto do endpoint
    para o schema acordado — sem lógica de rede, arquivo ou paginação.
    """

    # ── primitivos de extração ───────────────────────────────────────────────

    def binding_value(self, item: dict, chave: str) -> str | None:
        """Extrai o valor textual de um binding SPARQL, quando presente."""

        valor = item.get(chave)
        if not isinstance(valor, dict):
            return None
        return valor.get("value")

    def codigo_da_uri(self, uri: str | None) -> str | None:
        """Extrai o último segmento significativo de uma URI RDF."""

        if not uri:
            return None
        return uri.rstrip("/").split("/")[-1]

    # ── mapeamento principal ─────────────────────────────────────────────────

    def transformar(self, ano: int, item: dict) -> dict:
        """Achata um binding SPARQL no formato de saída do projeto."""

        bv = self.binding_value  # alias local para brevidade

        item_uri      = bv(item, "item")
        funcao_uri    = bv(item, "funcao")
        subfuncao_uri = bv(item, "subfuncao")
        programa_uri  = bv(item, "programa")
        acao_uri      = bv(item, "acao")
        unidade_uri   = bv(item, "unidade")
        fonte_uri     = bv(item, "fonte")
        gnd_uri       = bv(item, "gnd")
        modalidade_uri = bv(item, "modalidade")
        elemento_uri  = bv(item, "elemento")

        return {
            "ano": ano,
            "uri_item": item_uri,
            "grafo_orcamentario_uri": f"http://orcamento.dados.gov.br/{ano}/",
            "uri_funcao": funcao_uri,
            "codigo_funcao": self.codigo_da_uri(funcao_uri),
            "funcao": bv(item, "funcao_nome"),
            "uri_subfuncao": subfuncao_uri,
            "codigo_subfuncao": self.codigo_da_uri(subfuncao_uri),
            "subfuncao": bv(item, "subfuncao_nome"),
            "uri_programa": programa_uri,
            "codigo_programa": self.codigo_da_uri(programa_uri),
            "programa": bv(item, "programa_nome"),
            "uri_acao": acao_uri,
            "codigo_acao": self.codigo_da_uri(acao_uri),
            "acao": bv(item, "acao_nome"),
            "uri_unidade_orcamentaria": unidade_uri,
            "codigo_unidade_orcamentaria": self.codigo_da_uri(unidade_uri),
            "unidade_orcamentaria": bv(item, "unidade_nome"),
            "uri_fonte": fonte_uri,
            "codigo_fonte": self.codigo_da_uri(fonte_uri),
            "fonte": bv(item, "fonte_nome"),
            "uri_gnd": gnd_uri,
            "codigo_gnd": self.codigo_da_uri(gnd_uri),
            "gnd": bv(item, "gnd_nome"),
            "uri_modalidade": modalidade_uri,
            "codigo_modalidade": self.codigo_da_uri(modalidade_uri),
            "modalidade": bv(item, "modalidade_nome"),
            "uri_elemento": elemento_uri,
            "codigo_elemento": self.codigo_da_uri(elemento_uri),
            "elemento": bv(item, "elemento_nome"),
            "orgao_origem": "siop",
            "valor_pago": bv(item, "valorPago"),
            "valor_empenhado": bv(item, "valorEmpenhado"),
            "valor_liquidado": bv(item, "valorLiquidado"),
        }