export type Snapshot = {
  meta: SnapshotMeta;
  hero: HeroSection;
  highlights: HighlightCard[];
  coverage: CoverageCard[];
  rankings: RankingGroups;
  feed: FeedCard[];
};

export type SnapshotMeta = {
  generated_at: string;
  title: string;
  sources: string[];
  coverage_years: number[];
  notes: string[];
  ui: UiPayload;
};

export type UiPayload = {
  eyebrow: string;
  refresh_label: string;
  feed_title: string;
  feed_subtitle: string;
  search_label: string;
  search_placeholder: string;
  guide_title: string;
  guide_body: string;
  methodology_title: string;
  empty_feed_message: string;
  coverage_title: string;
  highlights_title: string;
  suppliers_title: string;
  agents_title: string;
  expenses_title: string;
};

export type HeroSection = {
  eyebrow: string;
  headline: string;
  subheadline: string;
  metrics: MetricCard[];
};

export type MetricCard = {
  label: string;
  value: string;
  detail: string;
  tone: string;
};

export type HighlightCard = {
  title: string;
  value: string;
  detail: string;
};

export type CoverageCard = {
  source: string;
  total: string;
  records: number;
  agents: number;
  suppliers: number;
  focus: string;
};

export type RankingGroups = {
  fornecedores: RankingItem[];
  agentes: RankingItem[];
  tipos_despesa: RankingItem[];
  ufs: RankingItem[];
};

export type RankingItem = {
  label: string;
  value: string;
  extra: string | null;
  sources: string[];
  share: number;
};

export type FeedCard = {
  source: string;
  period: string;
  headline: string;
  body: string;
  actor: string;
  actor_meta: string;
  supplier: string;
  supplier_doc: string | null;
  amount: string;
  expense_type: string;
  tags: string[];
};
