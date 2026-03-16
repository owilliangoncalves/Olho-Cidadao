import type { VariantePainelEstado, VisualPainelEstado } from "../types";

/** Resolve as classes visuais de um painel de estado sem acoplar a UI. */
export function montarVisualPainelEstado(
  variante: VariantePainelEstado = "neutro",
): VisualPainelEstado {
  if (variante === "erro") {
    return {
      classNamePainel: "max-w-lg border border-red-400/20 bg-red-300/8",
      classNameSobrelinha:
        "text-[11px] uppercase tracking-[0.28em] text-red-200",
      classNameDescricao: "mt-3 text-sm leading-7 text-stone-200",
      classNameReservaSobrelinha: "mx-auto h-3 w-28 rounded-full bg-white/10",
      classNameReservaTitulo:
        "mx-auto mt-3 h-8 w-72 max-w-full rounded-full bg-white/10",
      classNameReservaDescricao:
        "mx-auto mt-3 h-4 w-80 max-w-full rounded-full bg-white/8",
    };
  }

  return {
    classNamePainel: "border border-white/10 bg-white/5 text-center",
    classNameSobrelinha:
      "text-[11px] uppercase tracking-[0.28em] text-stone-500",
    classNameDescricao: "mt-3 text-sm text-stone-300",
    classNameReservaSobrelinha: "mx-auto h-3 w-28 rounded-full bg-white/10",
    classNameReservaTitulo:
      "mx-auto mt-3 h-8 w-72 max-w-full rounded-full bg-white/10",
    classNameReservaDescricao:
      "mx-auto mt-3 h-4 w-80 max-w-full rounded-full bg-white/8",
  };
}
