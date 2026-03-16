/**
 * Seção de comparativos e rankings.
 *
 * Organiza rankings em subtabs para evitar sobrecarga visual no desktop e
 * manter uma pergunta analítica por vez.
 */
import { BarChart3 } from "lucide-react";

import { ListaLeituraCurta } from "../components/dashboard/ListaLeituraCurta";
import { MenuSecundario } from "../components/dashboard/MenuSecundario";
import { MolduraSecao } from "../components/dashboard/MolduraSecao";
import { PainelInfo } from "../components/dashboard/PainelInfo";
import { RankingList } from "../components/RankingList";
import { montarModeloSecaoRankings } from "../lib/montarModeloSecaoRankings";
import type { AbaRanking, SecaoRankingsProps } from "../types";

/** Renderiza os rankings com navegação interna por categoria. */
export function SecaoRankings({
  snapshot,
  activeTab,
  onChangeTab,
}: SecaoRankingsProps) {
  const modelo = montarModeloSecaoRankings(snapshot, activeTab);

  return (
    <MolduraSecao
      eyebrow={modelo.moldura.eyebrow}
      title={modelo.moldura.title}
      description={modelo.moldura.description}
    >
      <MenuSecundario
        value={activeTab}
        onValueChange={(value) => onChangeTab(value as AbaRanking)}
        items={modelo.abasRanking}
      />

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <RankingList
          eyebrow={modelo.painelAtivo.eyebrow}
          title={modelo.painelAtivo.title}
          description={modelo.painelAtivo.description}
          items={modelo.painelAtivo.items}
          heightClass="h-[34rem]"
          className="bg-[#0d1018]/82"
        />

        <div className="space-y-4">
          <PainelInfo
            eyebrow={modelo.ajuda.eyebrow}
            title={modelo.ajuda.title}
            description={modelo.ajuda.description}
            icon={<BarChart3 size={18} />}
          />
          <ListaLeituraCurta
            eyebrow={modelo.leituraCurta.eyebrow}
            items={modelo.leituraCurta.items}
          />
        </div>
      </div>
    </MolduraSecao>
  );
}
