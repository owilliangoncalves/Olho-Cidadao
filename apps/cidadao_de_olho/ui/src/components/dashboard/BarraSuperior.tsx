import { Eye } from "lucide-react";

import type { BarraSuperiorProps } from "../../types";

/** Cabeçalho persistente da experiência pública. */
export function BarraSuperior({
  modelo,
  onChangeSection,
}: BarraSuperiorProps) {
  return (
    <header className="sticky top-4 z-20 rounded-[1.9rem] border border-white/8 bg-[#0d1018]/72 px-4 py-3 shadow-[0_22px_70px_rgba(4,8,15,0.28)] backdrop-blur-xl md:px-5">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-[1.3rem] bg-[linear-gradient(135deg,#f6b019,#d95e31_50%,#26b4a8)] shadow-[0_10px_28px_rgba(230,153,35,0.28)]">
            <Eye size={20} />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold tracking-[-0.04em] text-white md:text-xl">
              {modelo.titulo}
            </h1>
            <p className="mt-1 text-xs text-stone-400">{modelo.subtitulo}</p>
          </div>
        </div>

        <nav
          aria-label={modelo.rotuloAriaNavegacao}
          className="order-3 -mx-1 overflow-x-auto px-1 xl:order-2 xl:flex-1 xl:px-4"
        >
          <div className="inline-flex min-w-max items-center gap-1 rounded-full border border-white/8 bg-black/20 p-1">
            {modelo.navegacao.map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => onChangeSection(item.value)}
                title={item.dica}
                className={`rounded-full px-4 py-2 text-sm transition ${
                  item.ativo
                    ? "bg-white/10 text-white"
                    : "text-stone-400 hover:bg-white/6 hover:text-stone-200"
                }`}
              >
                <span className="whitespace-nowrap font-medium">
                  {item.label}
                </span>
              </button>
            ))}
          </div>
        </nav>

        <div className="order-2 flex items-center gap-2 text-xs text-stone-400 xl:order-3 xl:justify-end">
          <span className="inline-flex size-2 rounded-full bg-teal-300 shadow-[0_0_14px_rgba(45,212,191,0.9)]" />
          <span className="whitespace-nowrap">{modelo.atualizadoEm}</span>
        </div>
      </div>
    </header>
  );
}
