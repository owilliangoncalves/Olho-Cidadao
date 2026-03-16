import type { SecaoPrincipal } from "./contratosPublicos";

export type MetricaHeroiModelo = {
  id: string;
  label: string;
  value: string;
  detail: string;
  className: string;
};

export type NotaPainelModelo = {
  id: string;
  texto: string;
};

export type ItemLeituraCurtaModelo = {
  id: string;
  ordem: string;
  rotulo: string;
  valor: string;
  extra?: string | null;
};

export type CartaoDestaqueModelo = {
  id: string;
  titulo: string;
  valor: string;
  detalhe: string;
};

export type CartaoCoberturaModelo = {
  id: string;
  fonte: string;
  total: string;
  foco: string;
  estatisticas: string[];
};

export type ItemNavegacaoBarra = {
  value: SecaoPrincipal;
  label: string;
  dica: string;
  ativo: boolean;
};

export type BarraSuperiorModelo = {
  titulo: string;
  subtitulo: string;
  atualizadoEm: string;
  rotuloAriaNavegacao: string;
  navegacao: ItemNavegacaoBarra[];
};

export type VariantePainelEstado = "neutro" | "erro";

export type VisualPainelEstado = {
  classNamePainel: string;
  classNameSobrelinha: string;
  classNameDescricao: string;
  classNameReservaSobrelinha: string;
  classNameReservaTitulo: string;
  classNameReservaDescricao: string;
};

export type AcaoPainelMensagem = {
  rotulo?: string;
  rotuloAria: string;
  mostrarIconeAtualizar?: boolean;
  aoClicar: () => void;
};

export type PainelMensagemModelo = {
  variante?: VariantePainelEstado;
  sobrelinha?: string;
  titulo?: string;
  descricao?: string;
  visual: VisualPainelEstado;
  acao?: AcaoPainelMensagem;
};

export type BlocoInfoFeedProps = {
  label: string;
  value: string;
  detail: string;
  accent: string;
};

export type ModeloFeedCard = {
  source: string;
  period: string;
  headline: string;
  body: string;
  expenseType: string;
  accentClassName: string;
  usaIconeInstitucional: boolean;
  blocosInfo: BlocoInfoFeedProps[];
  tags: string[];
  tooltipTag: string;
};

export type LinhaRankingModelo = {
  id: string;
  posicao: string;
  rotulo: string;
  descricao?: string;
  valor: string;
  percentualBarra: number;
  mostrarSeparador: boolean;
};
