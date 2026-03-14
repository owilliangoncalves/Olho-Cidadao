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
import { MolduraSecao } from "../components/dashboard/Estrutura";
import {
  BotaoMetodologia,
  PainelInfo,
} from "../components/dashboard/Paineis";
import { RankingList } from "../components/RankingList";
import { abasFonte, type FiltroFonte, socialConfig } from "../config/social";
import { chaveFeed } from "../lib/feed";
import type { FeedCard as FeedCardModel, Snapshot } from "../types";

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
}: {
  snapshot: Snapshot;
  generatedAt: string;
  source: FiltroFonte;
  query: string;
  refreshing: boolean;
  filteredFeed: FeedCardModel[];
  onSourceChange: (value: FiltroFonte) => void;
  onQueryChange: (value: string) => void;
  onRefresh: () => void;
}) {
  const ui = snapshot.meta.ui;

  return (
    <MolduraSecao
      eyebrow={ui.feed_title}
      title={ui.feed_subtitle}
      description="A timeline mostra um registro por vez, com contexto para o cidadão entender quem gastou, com quem, em que fonte e quando."
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <BotaoMetodologia
            title={ui.methodology_title}
            description={socialConfig.inspector.methodologyHint}
            notes={snapshot.meta.notes}
          />
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-full border border-amber-400/35 bg-amber-300/12 px-4 py-2 text-sm font-medium text-amber-100 transition hover:bg-amber-300/18 disabled:cursor-wait disabled:opacity-80"
          >
            <RefreshCcw className={refreshing ? "animate-spin" : ""} size={16} />
            {refreshing ? "Atualizando..." : ui.refresh_label}
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
                {abasFonte.map((tab) => (
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
                  {ui.search_label}
                </p>
                <input
                  value={query}
                  onChange={(event) => onQueryChange(event.target.value)}
                  placeholder={ui.search_placeholder}
                  className="mt-1 w-full bg-transparent text-sm text-white outline-none placeholder:text-stone-500"
                />
              </div>
            </label>
          </div>

          <ScrollArea.Root className="overflow-hidden rounded-[2rem] border border-white/8 bg-[#0a0d15]/65">
            <ScrollArea.Viewport className="h-[calc(100vh-22rem)] min-h-[36rem]">
              <div className="space-y-4 p-4">
                {filteredFeed.length ? (
                  filteredFeed.map((item) => (
                    <FeedCard key={chaveFeed(item)} item={item} />
                  ))
                ) : (
                  <div className="rounded-[2rem] border border-dashed border-white/12 bg-white/4 px-6 py-16 text-center text-stone-300">
                    {ui.empty_feed_message}
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
            eyebrow={socialConfig.inspector.liveLabel}
            title="Leitura em tempo real do recorte"
            description={`Atualizado em ${generatedAt}. A timeline mostra ${filteredFeed.length} cards no filtro atual.`}
            icon={<Eye size={18} />}
          />
          <PainelInfo
            eyebrow="Filtro atual"
            title={source === "all" ? "Todas as fontes" : source}
            description={
              query
                ? `A busca ativa esta lendo o termo "${query}".`
                : "Use busca e abas para reduzir o ruído sem perder contexto."
            }
            icon={<Search size={18} />}
          />
          <RankingList
            eyebrow={socialConfig.inspector.rankingLabel}
            title={ui.suppliers_title}
            description="Uma leitura curta de quem mais aparece no radar."
            items={snapshot.rankings.fornecedores.slice(0, 6)}
            heightClass="h-[22rem]"
          />
        </div>
      </div>
    </MolduraSecao>
  );
}
