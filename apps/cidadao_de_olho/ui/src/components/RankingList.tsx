/**
 * Lista rolável de rankings usada nas áreas de visão rápida e comparativos.
 */
import * as ScrollArea from "@radix-ui/react-scroll-area";

import { montarLinhasRanking } from "../lib/montarLinhasRanking";
import type { RankingListProps } from "../types";
import { LinhaRanking } from "./LinhaRanking";

/** Renderiza um painel de ranking com barra de participação. */
export function RankingList({
  title,
  eyebrow,
  items,
  description,
  heightClass = "h-[16.5rem]",
  className = "",
}: RankingListProps) {
  const linhas = montarLinhasRanking(title, items);

  return (
    <section
      className={`rounded-[2rem] border border-white/8 bg-white/5 p-4 backdrop-blur-sm ${className}`}
    >
      <p className="text-[11px] uppercase tracking-[0.22em] text-stone-500">{eyebrow}</p>
      <h3 className="mt-2 text-lg font-semibold text-white">{title}</h3>
      {description ? (
        <p className="mt-2 text-sm leading-6 text-stone-400">{description}</p>
      ) : null}

      <ScrollArea.Root className={`mt-4 overflow-hidden ${heightClass}`}>
        <ScrollArea.Viewport className="size-full">
          <div className="space-y-4 pr-3">
            {linhas.map((item) => (
              <LinhaRanking
                key={item.id}
                item={item}
              />
            ))}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar
          orientation="vertical"
          className="flex w-2 touch-none select-none rounded-full bg-white/4 p-[1px]"
        >
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-white/18" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}
