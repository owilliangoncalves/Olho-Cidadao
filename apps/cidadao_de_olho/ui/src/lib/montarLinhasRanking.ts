import type { LinhaRankingModelo, RankingItem } from "../types";

/** Prepara as linhas do ranking com textos e largura visual já resolvidos. */
export function montarLinhasRanking(
  titulo: string,
  itens: RankingItem[],
): LinhaRankingModelo[] {
  return itens.map((item, indice) => ({
    id: `${titulo}-${item.label}-${indice}`,
    posicao: `${indice + 1}.`,
    rotulo: item.label,
    descricao: [item.extra, item.sources.join(" • ")].filter(Boolean).join(" • "),
    valor: item.value,
    percentualBarra: Math.max(item.share, 8),
    mostrarSeparador: indice < itens.length - 1,
  }));
}
