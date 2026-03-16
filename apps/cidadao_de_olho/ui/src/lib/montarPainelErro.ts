import type { PainelMensagemModelo, UiPayload } from "../types";

import { montarVisualPainelEstado } from "./montarVisualPainelEstado";

/** Traduz o payload da interface em um painel de erro com ação. */
export function montarPainelErro(
  message: string,
  aoTentarNovamente: () => void,
  ui?: UiPayload | null,
): PainelMensagemModelo {
  return {
    variante: "erro",
    sobrelinha: ui?.textos.estados.falha_sobrelinha,
    titulo: ui?.textos.estados.falha_titulo,
    descricao: message,
    visual: montarVisualPainelEstado("erro"),
    acao: {
      rotulo: ui?.textos.estados.botao_tentar_novamente,
      rotuloAria: ui?.textos.estados.botao_tentar_novamente ?? message,
      mostrarIconeAtualizar: true,
      aoClicar: aoTentarNovamente,
    },
  };
}
