import * as Separator from "@radix-ui/react-separator";

import type { LinhaRankingProps } from "../types";

/** Linha visual individual usada dentro das listas de ranking. */
export function LinhaRanking({ item }: LinhaRankingProps) {
  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-white">
            {item.posicao} {item.rotulo}
          </p>
          {item.descricao ? (
            <p className="mt-1 break-words text-xs text-stone-400">
              {item.descricao}
            </p>
          ) : null}
        </div>
        <span className="max-w-[9rem] break-words text-right text-sm font-semibold text-stone-200">
          {item.valor}
        </span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-amber-400 via-orange-300 to-teal-300"
          style={{ width: `${item.percentualBarra}%` }}
        />
      </div>
      {item.mostrarSeparador ? (
        <Separator.Root className="mt-4 h-px bg-white/8" decorative />
      ) : null}
    </div>
  );
}
