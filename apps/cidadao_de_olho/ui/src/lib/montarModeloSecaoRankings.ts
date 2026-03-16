import { montarAbasRanking } from "../config/montarAbasRanking";
import type { AbaRanking, RankingItem, Snapshot } from "../types";

import { montarListaLeituraCurta } from "./montarListaLeituraCurta";

/** Prepara os dados da seção de rankings para a camada visual. */
export function montarModeloSecaoRankings(
  snapshot: Snapshot,
  activeTab: AbaRanking,
) {
  const ui = snapshot.meta.ui;
  const textosPagina = ui.textos.rankings;
  const textosCompartilhados = ui.textos.compartilhado;
  const abasRanking = montarAbasRanking(ui.textos);
  const paineis: Record<
    AbaRanking,
    {
      title: string;
      eyebrow: string;
      description: string;
      items: RankingItem[];
    }
  > = {
    fornecedores: {
      title: ui.suppliers_title,
      eyebrow: textosPagina.sobrelinha_painel_fornecedores,
      description: textosPagina.descricao_painel_fornecedores,
      items: snapshot.rankings.fornecedores,
    },
    agentes: {
      title: ui.agents_title,
      eyebrow: textosPagina.sobrelinha_painel_agentes,
      description: textosPagina.descricao_painel_agentes,
      items: snapshot.rankings.agentes,
    },
    tipos: {
      title: ui.expenses_title,
      eyebrow: textosPagina.sobrelinha_painel_tipos,
      description: textosPagina.descricao_painel_tipos,
      items: snapshot.rankings.tipos_despesa,
    },
    ufs: {
      title: textosPagina.titulo_painel_ufs,
      eyebrow: textosPagina.sobrelinha_painel_ufs,
      description: textosPagina.descricao_painel_ufs,
      items: snapshot.rankings.ufs,
    },
  };

  const painelAtivo = paineis[activeTab];

  return {
    moldura: {
      eyebrow: textosPagina.sobrelinha_secao,
      title: textosPagina.titulo_secao,
      description: textosPagina.descricao_secao,
    },
    abasRanking,
    painelAtivo,
    ajuda: {
      eyebrow: textosPagina.sobrelinha_ajuda,
      title: textosPagina.titulo_ajuda,
      description: textosPagina.descricao_ajuda,
    },
    leituraCurta: {
      eyebrow: textosCompartilhados.sobrelinha_leitura_curta,
      items: montarListaLeituraCurta(painelAtivo.items.slice(0, 3)),
    },
  };
}
