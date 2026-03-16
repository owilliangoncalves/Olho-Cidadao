import type { BotaoAcaoLeveProps } from "../../types";

/** Botão secundário leve usado em ações de navegação contextual. */
export function BotaoAcaoLeve({ label, onClick }: BotaoAcaoLeveProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-full border border-white/10 bg-white/6 px-4 py-2.5 text-sm text-stone-200 transition hover:bg-white/10"
    >
      {label}
    </button>
  );
}
