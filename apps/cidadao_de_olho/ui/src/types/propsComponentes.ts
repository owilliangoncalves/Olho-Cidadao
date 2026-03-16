import type { ReactNode } from "react";

import type {
  FeedCard,
  SecaoPrincipal,
  TextosFeedCard,
} from "./contratosPublicos";
import type {
  BarraSuperiorModelo,
  CartaoCoberturaModelo,
  CartaoDestaqueModelo,
  ItemLeituraCurtaModelo,
  LinhaRankingModelo,
  MetricaHeroiModelo,
  NotaPainelModelo,
} from "./modelosTela";

export type FeedCardProps = {
  item: FeedCard;
  textos: TextosFeedCard;
};

export type RankingListProps = {
  title: string;
  eyebrow: string;
  items: import("./contratosPublicos").RankingItem[];
  description?: string;
  heightClass?: string;
  className?: string;
};

export type LinhaRankingProps = {
  item: LinhaRankingModelo;
};

export type BarraSuperiorProps = {
  modelo: BarraSuperiorModelo;
  onChangeSection: (section: SecaoPrincipal) => void;
};

export type MolduraSecaoProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
};

export type PainelHeroiProps = {
  eyebrow: string;
  headline: string;
  subheadline: string;
  metrics: MetricaHeroiModelo[];
  actions?: ReactNode;
};

export type TrilhoGuiaProps = {
  eyebrow: string;
  title: string;
  body: string;
  notes: NotaPainelModelo[];
};

export type PainelInfoProps = {
  eyebrow: string;
  title: string;
  description: string;
  icon: ReactNode;
};

export type ItemMenuSecundario = {
  value: string;
  label: string;
};

export type MenuSecundarioProps = {
  value: string;
  onValueChange: (value: string) => void;
  items: ItemMenuSecundario[];
};

export type ListaLeituraCurtaProps = {
  eyebrow: string;
  items: ItemLeituraCurtaModelo[];
};

export type BotaoMetodologiaProps = {
  triggerLabel: string;
  title: string;
  description: string;
  notes: NotaPainelModelo[];
};

export type BotaoAcaoLeveProps = {
  label: string;
  onClick: () => void;
};

export type CartaoDestaqueProps = {
  item: CartaoDestaqueModelo;
};

export type CartaoCoberturaProps = {
  item: CartaoCoberturaModelo;
};

export type TextoEstadoProps = {
  texto?: string;
  titulo?: boolean;
  className: string;
  reservaClassName: string;
};
