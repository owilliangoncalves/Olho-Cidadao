/**
 * Seção de glossário em linguagem simples.
 *
 * Reúne explicações curtas para os principais termos usados no radar público,
 * reduzindo barreiras de leitura para pessoas que não trabalham com dados.
 */
import { useDeferredValue, useState } from "react";

import { BookOpenText, Search } from "lucide-react";

import { MolduraSecao } from "../components/dashboard/MolduraSecao";
import { PainelInfo } from "../components/dashboard/PainelInfo";
import { descricaoGrupoGlossario } from "../lib/descricaoGrupoGlossario";
import { montarModeloSecaoGlossario } from "../lib/montarModeloSecaoGlossario";
import type { SecaoGlossarioProps } from "../types";

/** Renderiza o glossário acessível do produto. */
export function SecaoGlossario({
  termos,
  textos,
}: SecaoGlossarioProps) {
  const [query, setQuery] = useState("");
  const queryAdiada = useDeferredValue(query.trim().toLowerCase());
  const modelo = montarModeloSecaoGlossario(termos, queryAdiada);

  return (
    <MolduraSecao
      eyebrow={textos.sobrelinha_secao}
      title={textos.titulo_secao}
      description={textos.descricao_secao}
    >
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-5">
          <section className="rounded-[1.8rem] border border-white/8 bg-[#101522]/72 p-4 backdrop-blur-sm">
            <label
              htmlFor="glossario-busca"
              className="flex items-center gap-3 rounded-[1.4rem] border border-white/8 bg-[#0a0d15]/72 px-4 py-3"
            >
              <Search size={16} className="text-stone-400" />
              <div className="min-w-0 flex-1">
                <p className="text-[10px] uppercase tracking-[0.24em] text-stone-500">
                  {textos.rotulo_busca}
                </p>
                <input
                  id="glossario-busca"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder={textos.placeholder_busca}
                  className="mt-1 w-full bg-transparent text-sm text-white outline-none placeholder:text-stone-500"
                />
              </div>
              <span className="rounded-full border border-white/8 bg-white/6 px-3 py-1 text-xs text-stone-300">
                {modelo.termosFiltrados.length} {textos.rotulo_contador_termos}
              </span>
            </label>
          </section>

          {modelo.gruposComResultados.length ? (
            <div className="space-y-6">
              {modelo.gruposComResultados.map(({ grupo, itens }) => (
                <section key={grupo}>
                  <h3 className="text-lg font-semibold text-white">{grupo}</h3>
                  <p className="mt-2 text-sm leading-6 text-stone-400">
                    {descricaoGrupoGlossario(grupo, textos)}
                  </p>

                  <dl className="mt-4 grid gap-4 lg:grid-cols-2">
                    {itens.map((item) => (
                      <div
                        key={item.termo}
                        className="rounded-[1.8rem] border border-white/8 bg-white/4 p-5 backdrop-blur-sm"
                      >
                        <dt className="text-lg font-semibold text-white">
                          {item.termo}
                        </dt>
                        <dd className="mt-3 text-sm leading-7 text-stone-200">
                          {item.definicao}
                        </dd>
                        <dd className="mt-4 rounded-[1.3rem] border border-white/8 bg-[#0a0d15]/72 px-4 py-3 text-sm leading-6 text-stone-300">
                          <span className="mr-2 text-[10px] uppercase tracking-[0.24em] text-stone-500">
                            {textos.rotulo_contexto}
                          </span>
                          {item.contexto}
                        </dd>
                        <div className="mt-4 flex flex-wrap gap-2">
                          {item.relacionados.map((relacionado) => (
                            <span
                              key={`${item.termo}-${relacionado}`}
                              className="rounded-full border border-white/8 bg-white/6 px-3 py-1 text-xs text-stone-300"
                            >
                              {relacionado}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </dl>
                </section>
              ))}
            </div>
          ) : (
            <div className="rounded-[1.8rem] border border-dashed border-white/12 bg-white/4 px-6 py-12 text-center text-stone-300">
              {textos.mensagem_vazia}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <PainelInfo
            eyebrow={textos.sobrelinha_leitura}
            title={textos.titulo_leitura}
            description={textos.descricao_leitura}
            icon={<BookOpenText size={18} />}
          />

          <section className="rounded-[1.8rem] border border-white/8 bg-[#101522]/72 p-5 backdrop-blur-sm">
            <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
              {textos.titulo_como_usar}
            </p>
            <div className="mt-4 space-y-3 text-sm leading-7 text-stone-300">
              <p>{textos.passo_1_como_usar}</p>
              <p>{textos.passo_2_como_usar}</p>
              <p>{textos.passo_3_como_usar}</p>
            </div>
          </section>

          <section className="rounded-[1.8rem] border border-white/8 bg-[#101522]/72 p-5 backdrop-blur-sm">
            <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
              {textos.titulo_dica}
            </p>
            <p className="mt-4 text-sm leading-7 text-stone-300">
              {textos.descricao_dica}
            </p>
          </section>
        </div>
      </div>
    </MolduraSecao>
  );
}
