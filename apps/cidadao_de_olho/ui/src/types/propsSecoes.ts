import type {
  AbaCobertura,
  AbaRanking,
  FeedCard,
  FiltroFonte,
  Snapshot,
  TermoGlossario,
  TextosGlossario,
} from "./contratosPublicos";

export type SecaoVisaoGeralProps = {
  snapshot: Snapshot;
  generatedAt: string;
  onJumpToFeed: () => void;
  onJumpToCoverage: () => void;
};

export type SecaoFeedProps = {
  snapshot: Snapshot;
  generatedAt: string;
  source: FiltroFonte;
  query: string;
  refreshing: boolean;
  filteredFeed: FeedCard[];
  onSourceChange: (value: FiltroFonte) => void;
  onQueryChange: (value: string) => void;
  onRefresh: () => void;
};

export type SecaoRankingsProps = {
  snapshot: Snapshot;
  activeTab: AbaRanking;
  onChangeTab: (value: AbaRanking) => void;
};

export type SecaoCoberturaProps = {
  snapshot: Snapshot;
  activeTab: AbaCobertura;
  onChangeTab: (value: AbaCobertura) => void;
};

export type SecaoGlossarioProps = {
  termos: TermoGlossario[];
  textos: TextosGlossario;
};
