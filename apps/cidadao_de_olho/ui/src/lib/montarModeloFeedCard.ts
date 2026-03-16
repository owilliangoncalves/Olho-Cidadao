import type { FeedCard, ModeloFeedCard, TextosFeedCard } from "../types";

import { sourceAccent } from "./sourceAccent";

/** Traduz o item bruto do feed para um modelo visual simples. */
export function montarModeloFeedCard(
  item: FeedCard,
  textos: TextosFeedCard,
): ModeloFeedCard {
  return {
    source: item.source,
    period: item.period,
    headline: item.headline,
    body: item.body,
    expenseType: item.expense_type,
    accentClassName: sourceAccent(item.source),
    usaIconeInstitucional: item.source === "Camara",
    blocosInfo: [
      {
        label: textos.cartao_feed_agente,
        value: item.actor,
        detail: item.actor_meta,
        accent: "from-sky-300/10 to-transparent",
      },
      {
        label: textos.cartao_feed_fornecedor,
        value: item.supplier,
        detail: item.supplier_doc ?? textos.cartao_feed_documento_ausente,
        accent: "from-amber-300/10 to-transparent",
      },
      {
        label: textos.cartao_feed_valor,
        value: item.amount,
        detail: item.expense_type,
        accent: "from-emerald-300/10 to-transparent",
      },
    ],
    tags: item.tags,
    tooltipTag: textos.tooltip_tag,
  };
}
