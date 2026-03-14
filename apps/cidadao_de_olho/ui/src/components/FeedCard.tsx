/**
 * Card principal da timeline pública.
 *
 * Este componente reúne a leitura “social” de um registro sem esconder
 * metadados essenciais como fonte, período, fornecedor e valor.
 */
import * as Avatar from "@radix-ui/react-avatar";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Building2, UserRound } from "lucide-react";

import type { FeedCard as FeedCardModel } from "../types";
import { sourceAccent } from "../lib/format";

type FeedCardProps = {
  item: FeedCardModel;
};

/** Renderiza um item do feed cívico. */
export function FeedCard({ item }: FeedCardProps) {
  return (
    <article className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#10131d]/92 p-5 shadow-[0_30px_80px_rgba(7,10,16,0.45)] backdrop-blur">
      <div
        className={`pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${sourceAccent(item.source)}`}
      />

      <div className="mb-5 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex items-center gap-3">
          <Avatar.Root className="flex size-12 items-center justify-center rounded-2xl border border-white/10 bg-white/6">
            <Avatar.Fallback className="flex size-full items-center justify-center text-stone-100">
              {item.source === "Camara" ? <Building2 size={18} /> : <UserRound size={18} />}
            </Avatar.Fallback>
          </Avatar.Root>

          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-stone-400">
              {item.source}
            </p>
            <p className="text-sm text-stone-300">{item.period}</p>
          </div>
        </div>

        <span className="max-w-full self-start rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.22em] text-stone-300">
          {item.expense_type}
        </span>
      </div>

      <h3 className="max-w-3xl break-words text-2xl font-semibold tracking-[-0.03em] text-white">
        {item.headline}
      </h3>
      <p className="mt-3 max-w-3xl text-[15px] leading-7 text-stone-300">
        {item.body}
      </p>

      <div className="mt-5 grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
        <InfoCard
          label="Agente"
          value={item.actor}
          detail={item.actor_meta}
          accent="from-sky-300/10 to-transparent"
        />
        <InfoCard
          label="Fornecedor"
          value={item.supplier}
          detail={item.supplier_doc ?? "documento nao informado"}
          accent="from-amber-300/10 to-transparent"
        />
        <InfoCard
          label="Valor"
          value={item.amount}
          detail={item.expense_type}
          accent="from-emerald-300/10 to-transparent"
        />
      </div>

      <Tooltip.Provider delayDuration={120}>
        <div className="mt-5 flex flex-wrap gap-2">
          {item.tags.map((tag) => (
            <Tooltip.Root key={`${item.headline}-${tag}`}>
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
                  Tag para navegar com mais contexto
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          ))}
        </div>
      </Tooltip.Provider>
    </article>
  );
}

type InfoCardProps = {
  label: string;
  value: string;
  detail: string;
  accent: string;
};

/**
 * Bloco auxiliar para destacar metadados essenciais do card.
 */
function InfoCard({ label, value, detail, accent }: InfoCardProps) {
  return (
    <div className={`min-w-0 rounded-[1.6rem] border border-white/8 bg-gradient-to-br ${accent} p-4`}>
      <p className="text-[11px] uppercase tracking-[0.24em] text-stone-400">{label}</p>
      <p className="mt-3 break-words text-base font-semibold text-white">{value}</p>
      <p className="mt-1 break-words text-sm text-stone-400">{detail}</p>
    </div>
  );
}
