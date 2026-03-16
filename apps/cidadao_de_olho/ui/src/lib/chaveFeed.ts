import type { FeedCard } from "../types";

/** Gera uma chave estável o bastante para renderização da timeline. */
export function chaveFeed(item: FeedCard): string {
  return `${item.source}-${item.period}-${item.actor}-${item.supplier}-${item.amount}`;
}
