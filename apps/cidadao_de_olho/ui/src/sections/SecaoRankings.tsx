/**
 * Seção de comparativos e rankings.
 *
 * Organiza rankings em subtabs para evitar sobrecarga visual no desktop e
 * manter uma pergunta analítica por vez.
 */
import { BarChart3 } from "lucide-react";

import { MolduraSecao } from "../components/dashboard/Estrutura";
import {
  ListaLeituraCurta,
  MenuSecundario,
  PainelInfo,
} from "../components/dashboard/Paineis";
import { RankingList } from "../components/RankingList";
import { abasRanking, type AbaRanking } from "../config/social";
import type { RankingItem, Snapshot } from "../types";

/** Renderiza os rankings com navegação interna por categoria. */
export function SecaoRankings({
  snapshot,
  activeTab,
  onChangeTab,
}: {
  snapshot: Snapshot;
  activeTab: AbaRanking;
  onChangeTab: (value: AbaRanking) => void;
}) {
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
      title: snapshot.meta.ui.suppliers_title,
      eyebrow: "Fornecedores",
      description:
        "Ranking consolidado de fornecedores que mais aparecem nas despesas visiveis.",
      items: snapshot.rankings.fornecedores,
    },
    agentes: {
      title: snapshot.meta.ui.agents_title,
      eyebrow: "Agentes",
      description:
        "Agentes publicos com maior volume no recorte atual das bases monitoradas.",
      items: snapshot.rankings.agentes,
    },
    tipos: {
      title: snapshot.meta.ui.expenses_title,
      eyebrow: "Tipos",
      description:
        "Classificações de despesa mais presentes na combinacao atual de Camara e Senado.",
      items: snapshot.rankings.tipos_despesa,
    },
    ufs: {
      title: "Mapa de UF",
      eyebrow: "UFs",
      description:
        "Distribuicao por unidade federativa.",
      items: snapshot.rankings.ufs,
    },
  };

  const painelAtivo = paineis[activeTab];

  return (
    <MolduraSecao
      eyebrow="Comparativos"
      title="Rankings com submenu"
      description="No desktop, os rankings agora ficam separados por submenu para evitar quatro painéis concorrendo pela mesma tela."
    >
      <MenuSecundario
        value={activeTab}
        onValueChange={(value) => onChangeTab(value as AbaRanking)}
        items={abasRanking}
      />

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <RankingList
          eyebrow={painelAtivo.eyebrow}
          title={painelAtivo.title}
          description={painelAtivo.description}
          items={painelAtivo.items}
          heightClass="h-[34rem]"
          className="bg-[#0d1018]/82"
        />

        <div className="space-y-4">
          <PainelInfo
            eyebrow="Leitura"
            title="Como usar este submenu"
            description="Cada submenu isola uma pergunta: quem recebe mais, quem gasta mais, que tipo pesa mais e quais UFs mais aparecem."
            icon={<BarChart3 size={18} />}
          />
          <ListaLeituraCurta items={painelAtivo.items.slice(0, 3)} />
        </div>
      </div>
    </MolduraSecao>
  );
}
