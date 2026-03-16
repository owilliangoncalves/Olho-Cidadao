import type { PainelMensagemModelo, UiPayload } from "../types";

import { montarVisualPainelEstado } from "./montarVisualPainelEstado";

/** Traduz o payload da interface em um painel de carregamento. */
export function montarPainelCarregamento(
  ui?: UiPayload | null,
): PainelMensagemModelo {
  return {
    variante: "neutro",
    sobrelinha: ui?.textos.estados.carregando_sobrelinha,
    titulo: ui?.textos.estados.carregando_titulo,
    descricao: ui?.textos.estados.carregando_descricao,
    visual: montarVisualPainelEstado("neutro"),
  };
}
