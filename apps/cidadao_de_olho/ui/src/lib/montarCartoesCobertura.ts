import type {
  CartaoCoberturaModelo,
  CoverageCard,
  TextosCompartilhados,
} from "../types";

/** Traduz a cobertura bruta em linhas textuais prontas para renderização. */
export function montarCartoesCobertura(
  cobertura: CoverageCard[],
  textos: Pick<
    TextosCompartilhados,
    | "cartao_cobertura_registros"
    | "cartao_cobertura_agentes"
    | "cartao_cobertura_fornecedores"
  >,
): CartaoCoberturaModelo[] {
  return cobertura.map((item, indice) => ({
    id: `${indice}-${item.source}`,
    fonte: item.source,
    total: item.total,
    foco: item.focus,
    estatisticas: [
      `${item.records} ${textos.cartao_cobertura_registros}`,
      `${item.agents} ${textos.cartao_cobertura_agentes}`,
      `${item.suppliers} ${textos.cartao_cobertura_fornecedores}`,
    ],
  }));
}
