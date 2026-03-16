import type { FeedCard, FiltroFonte } from "../types";

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
