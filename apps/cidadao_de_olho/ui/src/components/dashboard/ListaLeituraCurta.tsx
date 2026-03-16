import type { ListaLeituraCurtaProps } from "../../types";

/** Lista curta para destacar os três primeiros itens de um ranking. */
export function ListaLeituraCurta({
  eyebrow,
  items,
}: ListaLeituraCurtaProps) {
  return (
    <section className="rounded-[2rem] border border-white/8 bg-white/5 p-4 backdrop-blur-sm">
      <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
        {eyebrow}
      </p>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-[1.5rem] border border-white/8 bg-[#0a0d15]/72 p-4"
          >
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">
              {item.ordem}
            </p>
            <p className="mt-2 break-words text-lg font-semibold text-white">
              {item.rotulo}
            </p>
            <p className="mt-1 break-words text-sm text-stone-300">{item.valor}</p>
            {item.extra ? (
              <p className="mt-2 text-xs text-stone-500">{item.extra}</p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
