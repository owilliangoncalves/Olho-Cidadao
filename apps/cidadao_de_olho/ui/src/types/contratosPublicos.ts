export type Snapshot = {
  meta: SnapshotMeta;
  hero: HeroSection;
  highlights: HighlightCard[];
  coverage: CoverageCard[];
  rankings: RankingGroups;
  glossario: TermoGlossario[];
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
  textos: TextosConfig;
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

export type GrupoGlossario = "Leitura do dado" | "Interface" | "Metodo";

export type SecaoPrincipal =
  | "overview"
  | "feed"
  | "rankings"
  | "coverage"
  | "glossario";

export type AbaRanking = "fornecedores" | "agentes" | "tipos" | "ufs";

export type AbaCobertura = "fontes" | "destaques" | "notas";

export type FiltroFonte = "all" | "Camara" | "Senado";

export type TermoGlossario = {
  termo: string;
  grupo: GrupoGlossario;
  definicao: string;
  contexto: string;
  relacionados: string[];
};

export type TextosConfig = {
  barra_superior: TextosBarraSuperior;
  estados: TextosEstados;
  compartilhado: TextosCompartilhados;
  visao_geral: TextosVisaoGeral;
  feed: TextosFeed;
  rankings: TextosRankings;
  cobertura: TextosCobertura;
  glossario: TextosGlossario;
};

export type TextosBarraSuperior = {
  subtitulo: string;
  atualizado_prefixo: string;
  cobertura_prefixo: string;
  cobertura_em_carga: string;
  rotulo_aria_navegacao: string;
};

export type TextosEstados = {
  carregando_sobrelinha: string;
  carregando_titulo: string;
  carregando_descricao: string;
  falha_sobrelinha: string;
  falha_titulo: string;
  botao_tentar_novamente: string;
};

export type TextosCompartilhados = {
  sobrelinha_guia_rapido: string;
  sobrelinha_leitura_curta: string;
  botao_metodologia: string;
  dica_metodologia: string;
  tooltip_tag: string;
  sobrelinha_ao_vivo: string;
  sobrelinha_quem_aparece_agora: string;
  cartao_cobertura_registros: string;
  cartao_cobertura_agentes: string;
  cartao_cobertura_fornecedores: string;
  cartao_feed_agente: string;
  cartao_feed_fornecedor: string;
  cartao_feed_valor: string;
  cartao_feed_documento_ausente: string;
};

export type TextosVisaoGeral = {
  rotulo_navegacao: string;
  sobrelinha_navegacao: string;
  descricao_navegacao: string;
  botao_abrir_feed: string;
  botao_ver_cobertura: string;
  sobrelinha_radar: string;
  titulo_radar: string;
  descricao_radar: string;
  titulo_leitura: string;
  descricao_leitura: string;
  titulo_cobertura: string;
  descricao_cobertura: string;
};

export type TextosFeed = {
  rotulo_navegacao: string;
  sobrelinha_navegacao: string;
  descricao_navegacao: string;
  descricao_secao: string;
  rotulo_atualizando: string;
  aba_todas: string;
  aba_camara: string;
  aba_senado: string;
  titulo_painel_leitura: string;
  descricao_painel_leitura: string;
  sobrelinha_painel_filtro: string;
  titulo_todas_fontes: string;
  descricao_painel_filtro_sem_busca: string;
  descricao_painel_filtro_com_busca: string;
  descricao_ranking: string;
};

export type TextosRankings = {
  rotulo_navegacao: string;
  sobrelinha_navegacao: string;
  descricao_navegacao: string;
  sobrelinha_secao: string;
  titulo_secao: string;
  descricao_secao: string;
  aba_fornecedores: string;
  aba_agentes: string;
  aba_tipos: string;
  aba_ufs: string;
  sobrelinha_painel_fornecedores: string;
  descricao_painel_fornecedores: string;
  sobrelinha_painel_agentes: string;
  descricao_painel_agentes: string;
  sobrelinha_painel_tipos: string;
  descricao_painel_tipos: string;
  titulo_painel_ufs: string;
  sobrelinha_painel_ufs: string;
  descricao_painel_ufs: string;
  sobrelinha_ajuda: string;
  titulo_ajuda: string;
  descricao_ajuda: string;
};

export type TextosCobertura = {
  rotulo_navegacao: string;
  sobrelinha_navegacao: string;
  descricao_navegacao: string;
  sobrelinha_secao: string;
  titulo_secao: string;
  descricao_secao: string;
  aba_fontes: string;
  aba_destaques: string;
  aba_notas: string;
  sobrelinha_contrato: string;
  titulo_contrato: string;
  descricao_contrato: string;
};

export type TextosGlossario = {
  rotulo_navegacao: string;
  sobrelinha_navegacao: string;
  descricao_navegacao: string;
  sobrelinha_secao: string;
  titulo_secao: string;
  descricao_secao: string;
  rotulo_busca: string;
  placeholder_busca: string;
  rotulo_contador_termos: string;
  mensagem_vazia: string;
  rotulo_contexto: string;
  sobrelinha_leitura: string;
  titulo_leitura: string;
  descricao_leitura: string;
  titulo_como_usar: string;
  passo_1_como_usar: string;
  passo_2_como_usar: string;
  passo_3_como_usar: string;
  titulo_dica: string;
  descricao_dica: string;
  descricao_grupo_leitura_do_dado: string;
  descricao_grupo_interface: string;
  descricao_grupo_metodo: string;
};

export type ItemNavegacaoPrimaria = {
  value: SecaoPrincipal;
  label: string;
  eyebrow: string;
  description: string;
};

export type ItemAbaFonte = {
  value: FiltroFonte;
  label: string;
};

export type ItemAbaRanking = {
  value: AbaRanking;
  label: string;
};

export type ItemAbaCobertura = {
  value: AbaCobertura;
  label: string;
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

export type TextosFeedCard = Pick<
  TextosCompartilhados,
  | "cartao_feed_agente"
  | "cartao_feed_fornecedor"
  | "cartao_feed_valor"
  | "cartao_feed_documento_ausente"
  | "tooltip_tag"
>;
