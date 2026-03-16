/**
 * Seção de entrada da aplicação.
 *
 * Resume hero, destaques, cobertura inicial e contexto editorial para quem
 * acabou de abrir o produto.
 */
import { Eye } from "lucide-react";

import { BotaoAcaoLeve } from "../components/dashboard/BotaoAcaoLeve";
import { CartaoCobertura } from "../components/dashboard/CartaoCobertura";
import { CartaoDestaque } from "../components/dashboard/CartaoDestaque";
import { MolduraSecao } from "../components/dashboard/MolduraSecao";
import { PainelHeroi } from "../components/dashboard/PainelHeroi";
import { PainelInfo } from "../components/dashboard/PainelInfo";
import { TrilhoGuia } from "../components/dashboard/TrilhoGuia";
import { montarModeloSecaoVisaoGeral } from "../lib/montarModeloSecaoVisaoGeral";
import type { SecaoVisaoGeralProps } from "../types";

/** Renderiza a visão geral inicial do `Olho Cidadão`. */
export function SecaoVisaoGeral({
  snapshot,
  generatedAt,
  onJumpToFeed,
  onJumpToCoverage,
}: SecaoVisaoGeralProps) {
  const modelo = montarModeloSecaoVisaoGeral(snapshot, generatedAt);

  return (
    <div className="space-y-5">
      <PainelHeroi
        eyebrow={modelo.heroi.eyebrow}
        headline={modelo.heroi.headline}
        subheadline={modelo.heroi.subheadline}
        metrics={modelo.heroi.metrics}
        actions={
          <>
            <BotaoAcaoLeve
              label={modelo.heroi.botaoAbrirFeed}
              onClick={onJumpToFeed}
            />
            <BotaoAcaoLeve
              label={modelo.heroi.botaoVerCobertura}
              onClick={onJumpToCoverage}
            />
          </>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <MolduraSecao
          eyebrow={modelo.radar.eyebrow}
          title={modelo.radar.title}
          description={modelo.radar.description}
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {modelo.radar.destaques.map((item) => (
              <CartaoDestaque key={item.id} item={item} />
            ))}
          </div>
        </MolduraSecao>

        <div className="space-y-4">
          <TrilhoGuia
            eyebrow={modelo.guia.eyebrow}
            title={modelo.guia.title}
            body={modelo.guia.body}
            notes={modelo.guia.notes}
          />
          <PainelInfo
            eyebrow={modelo.leitura.eyebrow}
            title={modelo.leitura.title}
            description={modelo.leitura.description}
            icon={<Eye size={18} />}
          />
        </div>
      </div>

      <MolduraSecao
        eyebrow={modelo.cobertura.eyebrow}
        title={modelo.cobertura.title}
        description={modelo.cobertura.description}
      >
        <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-4">
          {modelo.cobertura.cartoes.map((item) => (
            <CartaoCobertura
              key={item.id}
              item={item}
            />
          ))}
        </div>
      </MolduraSecao>
    </div>
  );
}
