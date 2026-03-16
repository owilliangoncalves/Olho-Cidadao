import { montarNavegacaoPrimaria } from "../config/montarNavegacaoPrimaria";
import type {
  BarraSuperiorModelo,
  SecaoPrincipal,
  TextosBarraSuperior,
  UiPayload,
} from "../types";

/** Traduz o contrato da interface pública para o modelo da barra superior. */
export function montarBarraSuperior(
  title: string,
  activeSection: SecaoPrincipal,
  generatedAt: string,
  years: number[],
  ui: UiPayload,
): BarraSuperiorModelo {
  const textosBarra = ui.textos.barra_superior;

  return {
    titulo: title,
    subtitulo: `${resumoCobertura(years, textosBarra)} • ${textosBarra.subtitulo}`,
    atualizadoEm: `${textosBarra.atualizado_prefixo} ${generatedAt}`,
    rotuloAriaNavegacao: textosBarra.rotulo_aria_navegacao,
    navegacao: montarNavegacaoPrimaria(ui.textos).map((item) => ({
      value: item.value,
      label: item.label,
      dica: `${item.eyebrow}: ${item.description}`,
      ativo: item.value === activeSection,
    })),
  };
}

function resumoCobertura(years: number[], textos: TextosBarraSuperior) {
  if (!years.length) {
    return textos.cobertura_em_carga;
  }

  const ordenados = [...years].sort((a, b) => a - b);

  if (ordenados.length === 1) {
    return `${textos.cobertura_prefixo} ${ordenados[0]}`;
  }

  return `${textos.cobertura_prefixo} ${ordenados[0]}-${ordenados[ordenados.length - 1]}`;
}
