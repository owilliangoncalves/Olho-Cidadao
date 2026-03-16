/**
 * Seção de cobertura, destaques e metodologia.
 *
 * Reúne os elementos que explicam de onde vêm os dados e como a leitura deve
 * ser interpretada pela população.
 */
import { ShieldAlert } from "lucide-react";

import { CartaoCobertura } from "../components/dashboard/CartaoCobertura";
import { CartaoDestaque } from "../components/dashboard/CartaoDestaque";
import { MenuSecundario } from "../components/dashboard/MenuSecundario";
import { MolduraSecao } from "../components/dashboard/MolduraSecao";
import { PainelInfo } from "../components/dashboard/PainelInfo";
import { TrilhoGuia } from "../components/dashboard/TrilhoGuia";
import { montarModeloSecaoCobertura } from "../lib/montarModeloSecaoCobertura";
import type { AbaCobertura, SecaoCoberturaProps } from "../types";

/** Renderiza a área de cobertura da aplicação com submenu interno. */
export function SecaoCobertura({
  snapshot,
  activeTab,
  onChangeTab,
}: SecaoCoberturaProps) {
  const modelo = montarModeloSecaoCobertura(snapshot);

  return (
    <MolduraSecao
      eyebrow={modelo.moldura.eyebrow}
      title={modelo.moldura.title}
      description={modelo.moldura.description}
    >
      <MenuSecundario
        value={activeTab}
        onValueChange={(value) => onChangeTab(value as AbaCobertura)}
        items={modelo.abasCobertura}
      />

      {activeTab === "fontes" ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {modelo.cobertura.map((item) => (
            <CartaoCobertura
              key={item.id}
              item={item}
            />
          ))}
        </div>
      ) : null}

      {activeTab === "destaques" ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {modelo.destaques.map((item) => (
            <CartaoDestaque key={item.id} item={item} />
          ))}
        </div>
      ) : null}

      {activeTab === "notas" ? (
        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <section className="rounded-[2rem] border border-white/8 bg-white/5 p-5 backdrop-blur-sm">
            <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
              {modelo.metodologiaTitle}
            </p>
            <div className="mt-4 space-y-3">
              {modelo.notasMetodologia.map((note) => (
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
              eyebrow={modelo.guia.eyebrow}
              title={modelo.guia.title}
              body={modelo.guia.body}
              notes={modelo.guia.notes}
            />
            <PainelInfo
              eyebrow={modelo.contrato.eyebrow}
              title={modelo.contrato.title}
              description={modelo.contrato.description}
              icon={<ShieldAlert size={18} />}
            />
          </div>
        </div>
      ) : null}
    </MolduraSecao>
  );
}
