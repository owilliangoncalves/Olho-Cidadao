/**
 * Seção da timeline pública.
 *
 * Aqui ficam a busca, as abas por fonte, o refresh manual e a lista rolável
 * dos cards do feed.
 */
import * as ScrollArea from "@radix-ui/react-scroll-area";
import * as Tabs from "@radix-ui/react-tabs";
import { Eye, RefreshCcw, Search } from "lucide-react";

import { FeedCard } from "../components/FeedCard";
import { BotaoMetodologia } from "../components/dashboard/BotaoMetodologia";
import { MolduraSecao } from "../components/dashboard/MolduraSecao";
import { PainelInfo } from "../components/dashboard/PainelInfo";
import { RankingList } from "../components/RankingList";
import { chaveFeed } from "../lib/chaveFeed";
import { montarModeloSecaoFeed } from "../lib/montarModeloSecaoFeed";
import type { FiltroFonte, SecaoFeedProps } from "../types";

/** Renderiza a seção principal de leitura contínua do produto. */
export function SecaoFeed({
  snapshot,
  generatedAt,
  source,
  query,
  refreshing,
  filteredFeed,
  onSourceChange,
  onQueryChange,
  onRefresh,
}: SecaoFeedProps) {
  const modelo = montarModeloSecaoFeed(
    snapshot,
    generatedAt,
    source,
    query,
    refreshing,
    filteredFeed,
  );

  return (
    <MolduraSecao
      eyebrow={modelo.moldura.eyebrow}
      title={modelo.moldura.title}
      description={modelo.moldura.description}
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <BotaoMetodologia
            triggerLabel={modelo.metodologia.triggerLabel}
            title={modelo.metodologia.title}
            description={modelo.metodologia.description}
            notes={modelo.metodologia.notes}
          />
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-full border border-amber-400/35 bg-amber-300/12 px-4 py-2 text-sm font-medium text-amber-100 transition hover:bg-amber-300/18 disabled:cursor-wait disabled:opacity-80"
          >
            <RefreshCcw className={refreshing ? "animate-spin" : ""} size={16} />
            {modelo.atualizacao.rotulo}
          </button>
        </div>
      }
    >
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          <div className="grid gap-3 rounded-[1.8rem] border border-white/8 bg-white/4 p-4 lg:grid-cols-[minmax(0,1fr)_360px]">
            <Tabs.Root
              value={source}
              onValueChange={(value) => onSourceChange(value as FiltroFonte)}
            >
              <Tabs.List className="inline-flex flex-wrap gap-2 rounded-full border border-white/8 bg-white/5 p-1">
                {modelo.filtros.abasFonte.map((tab) => (
                  <Tabs.Trigger
                    key={tab.value}
                    value={tab.value}
                    className="rounded-full px-4 py-2 text-sm font-medium text-stone-300 outline-none transition data-[state=active]:bg-white data-[state=active]:text-[#11151f]"
                  >
                    {tab.label}
                  </Tabs.Trigger>
                ))}
              </Tabs.List>
            </Tabs.Root>

            <label className="flex items-center gap-3 rounded-[1.5rem] border border-white/8 bg-[#0a0d15]/72 px-4 py-3">
              <Search size={16} className="text-stone-400" />
              <div className="min-w-0 flex-1">
                <p className="text-[10px] uppercase tracking-[0.24em] text-stone-500">
                  {modelo.filtros.searchLabel}
                </p>
                <input
                  value={query}
                  onChange={(event) => onQueryChange(event.target.value)}
                  placeholder={modelo.filtros.searchPlaceholder}
                  className="mt-1 w-full bg-transparent text-sm text-white outline-none placeholder:text-stone-500"
                />
              </div>
            </label>
          </div>

          <ScrollArea.Root className="overflow-hidden rounded-[2rem] border border-white/8 bg-[#0a0d15]/65">
            <ScrollArea.Viewport className="h-[calc(100vh-22rem)] min-h-[36rem]">
              <div className="space-y-4 p-4">
                {modelo.feed.itens.length ? (
                  modelo.feed.itens.map((item) => (
                    <FeedCard
                      key={chaveFeed(item)}
                      item={item}
                      textos={modelo.textosCompartilhados}
                    />
                  ))
                ) : (
                  <div className="rounded-[2rem] border border-dashed border-white/12 bg-white/4 px-6 py-16 text-center text-stone-300">
                    {modelo.feed.mensagemVazia}
                  </div>
                )}
              </div>
            </ScrollArea.Viewport>
            <ScrollArea.Scrollbar
              orientation="vertical"
              className="flex w-2 touch-none select-none rounded-full bg-white/4 p-[1px]"
            >
              <ScrollArea.Thumb className="relative flex-1 rounded-full bg-white/18" />
            </ScrollArea.Scrollbar>
          </ScrollArea.Root>
        </div>

        <div className="space-y-4">
          <PainelInfo
            eyebrow={modelo.painelLeitura.eyebrow}
            title={modelo.painelLeitura.title}
            description={modelo.painelLeitura.description}
            icon={<Eye size={18} />}
          />
          <PainelInfo
            eyebrow={modelo.painelFiltro.eyebrow}
            title={modelo.painelFiltro.title}
            description={modelo.painelFiltro.description}
            icon={<Search size={18} />}
          />
          <RankingList
            eyebrow={modelo.ranking.eyebrow}
            title={modelo.ranking.title}
            description={modelo.ranking.description}
            items={modelo.ranking.items}
            heightClass="h-[22rem]"
          />
        </div>
      </div>
    </MolduraSecao>
  );
}
