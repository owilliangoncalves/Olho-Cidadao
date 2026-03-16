import type { Snapshot } from "../types";

import { interpolarTexto } from "./interpolarTexto";
import { montarCartoesCobertura } from "./montarCartoesCobertura";
import { montarCartoesDestaque } from "./montarCartoesDestaque";
import { montarMetricasHeroi } from "./montarMetricasHeroi";
import { montarNotasPainel } from "./montarNotasPainel";

/** Prepara o conteúdo da visão geral sem derivação na camada visual. */
export function montarModeloSecaoVisaoGeral(
  snapshot: Snapshot,
  generatedAt: string,
) {
  const ui = snapshot.meta.ui;
  const textosPagina = ui.textos.visao_geral;
  const textosCompartilhados = ui.textos.compartilhado;
  const fontesAtivas = snapshot.meta.sources.join(" • ");

  return {
    heroi: {
      eyebrow: snapshot.hero.eyebrow,
      headline: snapshot.hero.headline,
      subheadline: snapshot.hero.subheadline,
      metrics: montarMetricasHeroi(snapshot.hero.metrics),
      botaoAbrirFeed: textosPagina.botao_abrir_feed,
      botaoVerCobertura: textosPagina.botao_ver_cobertura,
    },
    radar: {
      eyebrow: textosPagina.sobrelinha_radar,
      title: textosPagina.titulo_radar,
      description: textosPagina.descricao_radar,
      destaques: montarCartoesDestaque(snapshot.highlights),
    },
    guia: {
      eyebrow: textosCompartilhados.sobrelinha_guia_rapido,
      title: ui.guide_title,
      body: ui.guide_body,
      notes: montarNotasPainel(snapshot.meta.notes, 3),
    },
    leitura: {
      eyebrow: textosCompartilhados.sobrelinha_ao_vivo,
      title: textosPagina.titulo_leitura,
      description: interpolarTexto(textosPagina.descricao_leitura, {
        gerado_em: generatedAt,
        fontes_ativas: fontesAtivas,
      }),
    },
    cobertura: {
      eyebrow: ui.coverage_title,
      title: textosPagina.titulo_cobertura,
      description: textosPagina.descricao_cobertura,
      cartoes: montarCartoesCobertura(snapshot.coverage, textosCompartilhados),
    },
  };
}
