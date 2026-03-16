import type { PainelInfoProps } from "../../types";

/** Painel de apoio usado para contexto, status e orientação. */
export function PainelInfo({
  eyebrow,
  title,
  description,
  icon,
}: PainelInfoProps) {
  return (
    <section className="rounded-[1.8rem] border border-white/8 bg-[#101522]/72 p-4 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-2xl border border-white/10 bg-white/6 text-stone-100">
          {icon}
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-stone-500">
            {eyebrow}
          </p>
          <p className="mt-1 break-words text-base font-semibold text-white">
            {title}
          </p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-stone-300">{description}</p>
    </section>
  );
}
