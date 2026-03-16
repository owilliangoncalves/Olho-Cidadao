import type { CartaoDestaqueModelo, HighlightCard } from "../types";

/** Traduz os destaques do snapshot para um contrato visual simples. */
export function montarCartoesDestaque(
  destaques: HighlightCard[],
): CartaoDestaqueModelo[] {
  return destaques.map((item, indice) => ({
    id: `${indice}-${item.title}`,
    titulo: item.title,
    valor: item.value,
    detalhe: item.detail,
  }));
}
