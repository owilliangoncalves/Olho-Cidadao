import { montarAbasFonte } from "../config/montarAbasFonte";
import type { FeedCard, FiltroFonte, Snapshot } from "../types";

import { interpolarTexto } from "./interpolarTexto";
import { montarNotasPainel } from "./montarNotasPainel";

/** Prepara o conteúdo da seção de feed para a camada visual. */
export function montarModeloSecaoFeed(
  snapshot: Snapshot,
  generatedAt: string,
  source: FiltroFonte,
  query: string,
  refreshing: boolean,
  filteredFeed: FeedCard[],
) {
  const ui = snapshot.meta.ui;
  const textosPagina = ui.textos.feed;
  const textosCompartilhados = ui.textos.compartilhado;

  return {
    moldura: {
      eyebrow: ui.feed_title,
      title: ui.feed_subtitle,
      description: textosPagina.descricao_secao,
    },
    metodologia: {
      triggerLabel: textosCompartilhados.botao_metodologia,
      title: ui.methodology_title,
      description: textosCompartilhados.dica_metodologia,
      notes: montarNotasPainel(snapshot.meta.notes),
    },
    atualizacao: {
      rotulo: refreshing ? textosPagina.rotulo_atualizando : ui.refresh_label,
    },
    filtros: {
      abasFonte: montarAbasFonte(ui.textos),
      searchLabel: ui.search_label,
      searchPlaceholder: ui.search_placeholder,
    },
    feed: {
      mensagemVazia: ui.empty_feed_message,
      itens: filteredFeed,
    },
    painelLeitura: {
      eyebrow: textosCompartilhados.sobrelinha_ao_vivo,
      title: textosPagina.titulo_painel_leitura,
      description: interpolarTexto(textosPagina.descricao_painel_leitura, {
        gerado_em: generatedAt,
        quantidade_cards: filteredFeed.length,
      }),
    },
    painelFiltro: {
      eyebrow: textosPagina.sobrelinha_painel_filtro,
      title: source === "all" ? textosPagina.titulo_todas_fontes : source,
      description: query
        ? interpolarTexto(textosPagina.descricao_painel_filtro_com_busca, {
            termo: query,
          })
        : textosPagina.descricao_painel_filtro_sem_busca,
    },
    ranking: {
      eyebrow: textosCompartilhados.sobrelinha_quem_aparece_agora,
      title: ui.suppliers_title,
      description: textosPagina.descricao_ranking,
      items: snapshot.rankings.fornecedores.slice(0, 6),
    },
    textosCompartilhados,
  };
}
