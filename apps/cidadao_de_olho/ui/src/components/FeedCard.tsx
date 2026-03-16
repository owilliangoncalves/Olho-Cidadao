/**
 * Card principal da timeline pública.
 *
 * Este componente reúne a leitura “social” de um registro sem esconder
 * metadados essenciais como fonte, período, fornecedor e valor.
 */
import * as Avatar from "@radix-ui/react-avatar";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Building2, UserRound } from "lucide-react";

import { montarModeloFeedCard } from "../lib/montarModeloFeedCard";
import type { FeedCardProps } from "../types";
import { BlocoInfoFeed } from "./BlocoInfoFeed";

/** Renderiza um item do feed cívico. */
export function FeedCard({ item, textos }: FeedCardProps) {
  const modelo = montarModeloFeedCard(item, textos);

  return (
    <article className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#10131d]/92 p-5 shadow-[0_30px_80px_rgba(7,10,16,0.45)] backdrop-blur">
      <div
        className={`pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${modelo.accentClassName}`}
      />

      <div className="mb-5 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-center gap-3">
          <Avatar.Root className="flex size-12 items-center justify-center rounded-2xl border border-white/10 bg-white/6">
            <Avatar.Fallback className="flex size-full items-center justify-center text-stone-100">
              {modelo.usaIconeInstitucional ? (
                <Building2 size={18} />
              ) : (
                <UserRound size={18} />
              )}
            </Avatar.Fallback>
          </Avatar.Root>

          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-stone-400">
              {modelo.source}
            </p>
            <p className="text-sm text-stone-300">{modelo.period}</p>
          </div>
        </div>

        <span className="max-w-full self-start rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.22em] text-stone-300">
          {modelo.expenseType}
        </span>
      </div>

      <h3 className="max-w-3xl break-words text-2xl font-semibold tracking-[-0.03em] text-white">
        {modelo.headline}
      </h3>
      <p className="mt-3 max-w-3xl text-[15px] leading-7 text-stone-300">
        {modelo.body}
      </p>

      <div className="mt-5 grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
        {modelo.blocosInfo.map((bloco) => (
          <BlocoInfoFeed
            key={`${modelo.headline}-${bloco.label}`}
            label={bloco.label}
            value={bloco.value}
            detail={bloco.detail}
            accent={bloco.accent}
          />
        ))}
      </div>

      <Tooltip.Provider delayDuration={120}>
        <div className="mt-5 flex flex-wrap gap-2">
          {modelo.tags.map((tag) => (
            <Tooltip.Root key={`${modelo.headline}-${tag}`}>
              <Tooltip.Trigger asChild>
                <span className="cursor-default rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs text-stone-200">
                  #{tag}
                </span>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  sideOffset={8}
                  className="rounded-xl border border-white/10 bg-[#171a24] px-3 py-2 text-xs text-stone-200 shadow-xl"
                >
                  {modelo.tooltipTag}
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          ))}
        </div>
      </Tooltip.Provider>
    </article>
  );
}
