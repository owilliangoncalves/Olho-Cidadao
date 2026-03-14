/**
 * Utilitários de filtragem e identidade do feed.
 */
import type { FiltroFonte } from "../config/social";
import type { FeedCard } from "../types";

/** Aplica filtro textual e filtro por fonte sobre os cards do feed. */
export function filtrarFeed(
  feed: FeedCard[],
  query: string,
  source: FiltroFonte,
): FeedCard[] {
  const normalizedQuery = query.trim().toLowerCase();

  return feed.filter((item) => {
    const sourceMatches = source === "all" || item.source === source;
    if (!normalizedQuery) {
      return sourceMatches;
    }

    const haystack = [
      item.headline,
      item.body,
      item.actor,
      item.actor_meta,
      item.supplier,
      item.expense_type,
      item.tags.join(" "),
    ]
      .join(" ")
      .toLowerCase();

    return sourceMatches && haystack.includes(normalizedQuery);
  });
}

/** Gera uma chave estável o bastante para renderização da timeline. */
export function chaveFeed(item: FeedCard): string {
  return `${item.source}-${item.period}-${item.actor}-${item.supplier}-${item.amount}`;
}
