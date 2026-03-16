import type { BlocoInfoFeedProps } from "../types";

/** Bloco auxiliar para destacar metadados essenciais do card. */
export function BlocoInfoFeed({
  label,
  value,
  detail,
  accent,
}: BlocoInfoFeedProps) {
  return (
    <div
      className={`min-w-0 rounded-[1.6rem] border border-white/8 bg-gradient-to-br ${accent} p-4`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-stone-400">
        {label}
      </p>
      <p className="mt-3 break-words text-base font-semibold text-white">
        {value}
      </p>
      <p className="mt-1 break-words text-sm text-stone-400">{detail}</p>
    </div>
  );
}
