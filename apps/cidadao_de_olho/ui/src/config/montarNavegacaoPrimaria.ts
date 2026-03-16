import type { ItemNavegacaoPrimaria, TextosConfig } from "../types";

/** Navegação principal montada a partir dos textos do backend. */
export function montarNavegacaoPrimaria(
  textos: TextosConfig,
): ItemNavegacaoPrimaria[] {
  return [
    {
      value: "overview",
      label: textos.visao_geral.rotulo_navegacao,
      eyebrow: textos.visao_geral.sobrelinha_navegacao,
      description: textos.visao_geral.descricao_navegacao,
    },
    {
      value: "feed",
      label: textos.feed.rotulo_navegacao,
      eyebrow: textos.feed.sobrelinha_navegacao,
      description: textos.feed.descricao_navegacao,
    },
    {
      value: "rankings",
      label: textos.rankings.rotulo_navegacao,
      eyebrow: textos.rankings.sobrelinha_navegacao,
      description: textos.rankings.descricao_navegacao,
    },
    {
      value: "coverage",
      label: textos.cobertura.rotulo_navegacao,
      eyebrow: textos.cobertura.sobrelinha_navegacao,
      description: textos.cobertura.descricao_navegacao,
    },
    {
      value: "glossario",
      label: textos.glossario.rotulo_navegacao,
      eyebrow: textos.glossario.sobrelinha_navegacao,
      description: textos.glossario.descricao_navegacao,
    },
  ];
}
