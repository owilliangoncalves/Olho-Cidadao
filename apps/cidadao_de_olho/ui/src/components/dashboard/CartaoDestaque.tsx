import type { CartaoDestaqueProps } from "../../types";

/** Card curto de destaque usado em visão geral e cobertura. */
export function CartaoDestaque({ item }: CartaoDestaqueProps) {
  return (
    <article className="rounded-[1.7rem] border border-white/8 bg-white/4 p-5 backdrop-blur-sm">
      <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
        {item.titulo}
      </p>
      <p className="mt-3 break-words text-2xl font-semibold tracking-[-0.04em] text-white">
        {item.valor}
      </p>
      <p className="mt-3 text-sm leading-7 text-stone-300">{item.detalhe}</p>
    </article>
  );
}
