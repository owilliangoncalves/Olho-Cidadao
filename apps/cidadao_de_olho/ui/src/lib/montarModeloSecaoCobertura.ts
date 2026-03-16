import { montarAbasCobertura } from "../config/montarAbasCobertura";
import type { Snapshot } from "../types";

import { montarCartoesCobertura } from "./montarCartoesCobertura";
import { montarCartoesDestaque } from "./montarCartoesDestaque";
import { montarNotasPainel } from "./montarNotasPainel";

/** Prepara o conteúdo da seção de cobertura sem derivação na UI. */
export function montarModeloSecaoCobertura(snapshot: Snapshot) {
  const ui = snapshot.meta.ui;
  const textosPagina = ui.textos.cobertura;
  const textosCompartilhados = ui.textos.compartilhado;

  return {
    moldura: {
      eyebrow: textosPagina.sobrelinha_secao,
      title: textosPagina.titulo_secao,
      description: textosPagina.descricao_secao,
    },
    abasCobertura: montarAbasCobertura(ui.textos),
    cobertura: montarCartoesCobertura(snapshot.coverage, textosCompartilhados),
    destaques: montarCartoesDestaque(snapshot.highlights),
    notasMetodologia: snapshot.meta.notes,
    metodologiaTitle: ui.methodology_title,
    guia: {
      eyebrow: textosCompartilhados.sobrelinha_guia_rapido,
      title: ui.guide_title,
      body: ui.guide_body,
      notes: montarNotasPainel(snapshot.meta.notes, 3),
    },
    contrato: {
      eyebrow: textosPagina.sobrelinha_contrato,
      title: textosPagina.titulo_contrato,
      description: textosPagina.descricao_contrato,
    },
  };
}
