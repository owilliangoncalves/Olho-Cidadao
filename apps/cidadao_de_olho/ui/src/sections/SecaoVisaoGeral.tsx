/**
 * Seção de entrada da aplicação.
 *
 * Resume hero, destaques, cobertura inicial e contexto editorial para quem
 * acabou de abrir o produto.
 */
import { Eye, Landmark } from "lucide-react";

import {
  BotaoAcaoLeve,
  CartaoCobertura,
  CartaoDestaque,
  PainelHeroi,
  PainelInfo,
  TrilhoGuia,
} from "../components/dashboard/Paineis";
import { MolduraSecao } from "../components/dashboard/Estrutura";
import { socialConfig } from "../config/social";
import type { Snapshot } from "../types";

/** Renderiza a visão geral inicial do `Cidadão de Olho`. */
export function SecaoVisaoGeral({
  snapshot,
  generatedAt,
  onJumpToFeed,
  onJumpToCoverage,
}: {
  snapshot: Snapshot;
  generatedAt: string;
  onJumpToFeed: () => void;
  onJumpToCoverage: () => void;
}) {
  const ui = snapshot.meta.ui;

  return (
    <>
      <PainelHeroi
        eyebrow={snapshot.hero.eyebrow}
        headline={snapshot.hero.headline}
        subheadline={snapshot.hero.subheadline}
        metrics={snapshot.hero.metrics}
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <MolduraSecao
            eyebrow="Radar rápido"
            title="O que merece atenção primeiro"
            description="Agrupa os sinais mais fortes para facilitar a primeira leitura."
            actions={
              <div className="flex flex-wrap gap-2">
                <BotaoAcaoLeve label="Abrir timeline" onClick={onJumpToFeed} />
                <BotaoAcaoLeve
                  label="Ver cobertura"
                  onClick={onJumpToCoverage}
                />
              </div>
            }
          >
            <div className="grid gap-4 lg:grid-cols-2">
              {snapshot.highlights.map((item) => (
                <CartaoDestaque key={item.title} item={item} />
              ))}
            </div>
          </MolduraSecao>

          <MolduraSecao
            eyebrow={ui.coverage_title}
            title="Fontes e cobertura ativa"
            description="Cada bloco mostra o tamanho do recorte visivel e o foco da fonte no ambiente público."
          >
            <div className="grid gap-4 lg:grid-cols-2">
              {snapshot.coverage.map((item) => (
                <CartaoCobertura key={item.source} item={item} />
              ))}
            </div>
          </MolduraSecao>
        </div>

        <div className="space-y-5">
          <TrilhoGuia
            title={ui.guide_title}
            body={ui.guide_body}
            notes={snapshot.meta.notes}
          />
          <PainelInfo
            eyebrow={socialConfig.inspector.liveLabel}
            title={socialConfig.inspector.transparentLabel}
            description={`Atualizado em ${generatedAt}. Os cards levam fonte, periodo, agente, fornecedor e valor para que a leitura não perca rastreabilidade.`}
            icon={<Eye size={18} />}
          />
          <PainelInfo
            eyebrow="Fontes"
            title={snapshot.meta.sources.join(" • ")}
            description="Os dados exibidos aqui saem dos artefatos do ETL, mas a interface os reorganiza."
            icon={<Landmark size={18} />}
          />
        </div>
      </div>
    </>
  );
}
