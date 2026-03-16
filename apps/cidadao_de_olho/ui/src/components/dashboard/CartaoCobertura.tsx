import type { CartaoCoberturaProps } from "../../types";

/** Card de resumo de cobertura por fonte pública. */
export function CartaoCobertura({ item }: CartaoCoberturaProps) {
  return (
    <article className="rounded-[1.7rem] border border-white/8 bg-white/4 p-5 backdrop-blur-sm">
      <div className="flex flex-col gap-4">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
            {item.fonte}
          </p>
          <h3 className="mt-2 break-words text-xl font-semibold text-white">
            {item.total}
          </h3>
        </div>
        <div className="max-w-full self-start rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.2em] text-stone-300">
          {item.foco}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm text-stone-300">
        {item.estatisticas.map((estatistica) => (
          <span key={estatistica}>{estatistica}</span>
        ))}
      </div>
    </article>
  );
}
