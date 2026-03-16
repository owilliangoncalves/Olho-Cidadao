import type { ItemLeituraCurtaModelo, RankingItem } from "../types";

/** Prepara a leitura curta do ranking sem derivação na camada visual. */
export function montarListaLeituraCurta(
  itens: RankingItem[],
): ItemLeituraCurtaModelo[] {
  return itens.map((item, indice) => ({
    id: `${indice}-${item.label}`,
    ordem: `#${indice + 1}`,
    rotulo: item.label,
    valor: item.value,
    extra: item.extra,
  }));
}
