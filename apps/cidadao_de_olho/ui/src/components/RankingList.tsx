/**
 * Lista rolável de rankings usada nas áreas de visão rápida e comparativos.
 */
import * as ScrollArea from "@radix-ui/react-scroll-area";
import * as Separator from "@radix-ui/react-separator";

import type { RankingItem } from "../types";

type RankingListProps = {
  title: string;
  eyebrow: string;
  items: RankingItem[];
  description?: string;
  heightClass?: string;
  className?: string;
};

/** Renderiza um painel de ranking com barra de participação. */
export function RankingList({
  title,
  eyebrow,
  items,
  description,
  heightClass = "h-[16.5rem]",
  className = "",
}: RankingListProps) {
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
            {items.map((item, index) => (
              <div key={`${title}-${item.label}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="break-words text-sm font-medium text-white">
                      {index + 1}. {item.label}
                    </p>
                    <p className="mt-1 break-words text-xs text-stone-400">
                      {[item.extra, item.sources.join(" • ")].filter(Boolean).join(" • ")}
                    </p>
                  </div>
                  <span className="max-w-[9rem] break-words text-right text-sm font-semibold text-stone-200">
                    {item.value}
                  </span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/8">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-400 via-orange-300 to-teal-300"
                    style={{ width: `${Math.max(item.share, 8)}%` }}
                  />
                </div>
                {index < items.length - 1 ? (
                  <Separator.Root className="mt-4 h-px bg-white/8" decorative />
                ) : null}
              </div>
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
