/**
 * Seção de cobertura, destaques e metodologia.
 *
 * Reúne os elementos que explicam de onde vêm os dados e como a leitura deve
 * ser interpretada pela população.
 */
import { ShieldAlert } from "lucide-react";

import { MolduraSecao } from "../components/dashboard/Estrutura";
import {
  CartaoCobertura,
  CartaoDestaque,
  MenuSecundario,
  PainelInfo,
  TrilhoGuia,
} from "../components/dashboard/Paineis";
import { abasCobertura, type AbaCobertura } from "../config/social";
import type { Snapshot } from "../types";

/** Renderiza a área de cobertura da aplicação com submenu interno. */
export function SecaoCobertura({
  snapshot,
  activeTab,
  onChangeTab,
}: {
  snapshot: Snapshot;
  activeTab: AbaCobertura;
  onChangeTab: (value: AbaCobertura) => void;
}) {
  const ui = snapshot.meta.ui;

  return (
    <MolduraSecao
      eyebrow="Transparência"
      title="Cobertura e notas"
      description="A seção de cobertura reúne as fontes monitoradas, os destaques produzidos e a metodologia que sustenta a leitura."
    >
      <MenuSecundario
        value={activeTab}
        onValueChange={(value) => onChangeTab(value as AbaCobertura)}
        items={abasCobertura}
      />

      {activeTab === "fontes" ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {snapshot.coverage.map((item) => (
            <CartaoCobertura key={item.source} item={item} />
          ))}
        </div>
      ) : null}

      {activeTab === "destaques" ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {snapshot.highlights.map((item) => (
            <CartaoDestaque key={item.title} item={item} />
          ))}
        </div>
      ) : null}

      {activeTab === "notas" ? (
        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <section className="rounded-[2rem] border border-white/8 bg-white/5 p-5 backdrop-blur-sm">
            <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
              {ui.methodology_title}
            </p>
            <div className="mt-4 space-y-3">
              {snapshot.meta.notes.map((note) => (
                <div
                  key={note}
                  className="rounded-[1.5rem] border border-white/8 bg-[#0a0d15]/72 p-4 text-sm leading-7 text-stone-200"
                >
                  {note}
                </div>
              ))}
            </div>
          </section>

          <div className="space-y-4">
            <TrilhoGuia
              title={ui.guide_title}
              body={ui.guide_body}
              notes={snapshot.meta.notes}
            />
            <PainelInfo
              eyebrow="Contrato de leitura"
              title="Os cards não são conclusão automática"
              description="A interface ajuda a aproximar a linguagem visual da rede social, mas não reduz a exigência de contexto, fonte e rastreabilidade."
              icon={<ShieldAlert size={18} />}
            />
          </div>
        </div>
      ) : null}
    </MolduraSecao>
  );
}
