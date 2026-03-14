/**
 * Painéis reutilizáveis do dashboard.
 *
 * Estes componentes encapsulam os blocos visuais recorrentes da interface:
 * hero, guias laterais, menus secundários, diálogos e cartões auxiliares.
 */
import type { ReactNode } from "react";

import * as Dialog from "@radix-ui/react-dialog";
import * as Tabs from "@radix-ui/react-tabs";
import * as Separator from "@radix-ui/react-separator";
import { ShieldAlert, Sparkles, X } from "lucide-react";

import { socialConfig } from "../../config/social";
import { metricToneClass } from "../../lib/format";
import type { RankingItem, Snapshot } from "../../types";

/** Painel hero com headline principal e métricas de contexto. */
export function PainelHeroi(props: {
  eyebrow: string;
  headline: string;
  subheadline: string;
  metrics: Snapshot["hero"]["metrics"];
}) {
  return (
    <section className="relative overflow-hidden rounded-[2.8rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(246,176,25,0.26),_transparent_22%),radial-gradient(circle_at_bottom_right,_rgba(31,183,164,0.24),_transparent_25%),linear-gradient(135deg,_rgba(11,14,22,0.92),_rgba(22,27,39,0.95))] p-6 shadow-[0_40px_120px_rgba(4,8,15,0.48)] md:p-7 xl:p-8">
      <div className="absolute inset-y-0 right-[-120px] w-[320px] rounded-full bg-teal-300/10 blur-3xl" />
      <div className="relative">
        <p className="text-[11px] uppercase tracking-[0.3em] text-amber-200/85">
          {props.eyebrow}
        </p>
        <h2 className="mt-3 max-w-4xl text-4xl font-semibold tracking-[-0.06em] text-white md:text-5xl xl:text-6xl">
          {props.headline}
        </h2>
        <p className="mt-4 max-w-3xl text-base leading-8 text-stone-300 md:text-lg">
          {props.subheadline}
        </p>

        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {props.metrics.map((metric) => (
            <article
              key={metric.label}
              className={`rounded-[1.9rem] border p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] ${metricToneClass(metric.tone)}`}
            >
              <p className="text-[11px] uppercase tracking-[0.24em] text-stone-300/80">
                {metric.label}
              </p>
              <p className="mt-4 break-words text-3xl font-semibold tracking-[-0.04em] text-white">
                {metric.value}
              </p>
              <p className="mt-3 text-sm leading-6 text-stone-300">
                {metric.detail}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Bloco lateral com explicação rápida e notas metodológicas curtas. */
export function TrilhoGuia({
  title,
  body,
  notes,
}: {
  title: string;
  body: string;
  notes: string[];
}) {
  return (
    <section className="rounded-[2.2rem] border border-white/10 bg-[#0d1018]/80 p-5 shadow-[0_25px_80px_rgba(4,8,15,0.34)] backdrop-blur-xl">
      <p className="text-[11px] uppercase tracking-[0.26em] text-stone-500">
        Guia rápido
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-white">
        {title}
      </h2>
      <p className="mt-4 text-sm leading-7 text-stone-300">{body}</p>

      <Separator.Root className="my-5 h-px bg-white/8" decorative />

      <div className="space-y-3">
        {notes.slice(0, 3).map((note) => (
          <div key={note} className="rounded-[1.5rem] border border-white/8 bg-white/4 p-4">
            <div className="flex items-start gap-3">
              <Sparkles size={16} className="mt-1 shrink-0 text-amber-300" />
              <p className="text-sm leading-6 text-stone-200">{note}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/** Painel de apoio usado para contexto, status e orientação. */
export function PainelInfo({
  eyebrow,
  title,
  description,
  icon,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: ReactNode;
}) {
  return (
    <section className="rounded-[2rem] border border-white/8 bg-white/5 p-4 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="flex size-11 items-center justify-center rounded-2xl border border-white/10 bg-white/6 text-stone-100">
          {icon}
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-stone-500">
            {eyebrow}
          </p>
          <p className="mt-1 break-words text-base font-semibold text-white">
            {title}
          </p>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-stone-300">{description}</p>
    </section>
  );
}

/** Menu secundário padrão para subtabs internas das seções. */
export function MenuSecundario({
  value,
  onValueChange,
  items,
}: {
  value: string;
  onValueChange: (value: string) => void;
  items: Array<{ value: string; label: string }>;
}) {
  return (
    <Tabs.Root value={value} onValueChange={onValueChange}>
      <Tabs.List className="inline-flex flex-wrap gap-2 rounded-full border border-white/8 bg-white/5 p-1">
        {items.map((item) => (
          <Tabs.Trigger
            key={item.value}
            value={item.value}
            className="rounded-full px-4 py-2 text-sm font-medium text-stone-300 outline-none transition data-[state=active]:bg-white data-[state=active]:text-[#11151f]"
          >
            {item.label}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
    </Tabs.Root>
  );
}

/** Lista curta para destacar os três primeiros itens de um ranking. */
export function ListaLeituraCurta({ items }: { items: RankingItem[] }) {
  return (
    <section className="rounded-[2rem] border border-white/8 bg-white/5 p-4 backdrop-blur-sm">
      <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
        Leitura curta
      </p>
      <div className="mt-4 space-y-3">
        {items.map((item, index) => (
          <div
            key={item.label}
            className="rounded-[1.5rem] border border-white/8 bg-[#0a0d15]/72 p-4"
          >
            <p className="text-xs uppercase tracking-[0.24em] text-stone-500">
              #{index + 1}
            </p>
            <p className="mt-2 break-words text-lg font-semibold text-white">
              {item.label}
            </p>
            <p className="mt-1 break-words text-sm text-stone-300">{item.value}</p>
            {item.extra ? (
              <p className="mt-2 text-xs text-stone-500">{item.extra}</p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}

/** Botão que abre o modal de metodologia do produto. */
export function BotaoMetodologia({
  title,
  description,
  notes,
}: {
  title: string;
  description: string;
  notes: string[];
}) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-stone-200 transition hover:bg-white/10">
          <ShieldAlert size={16} />
          {socialConfig.inspector.methodologyTrigger}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-[#06070d]/70 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-[min(92vw,720px)] -translate-x-1/2 -translate-y-1/2 rounded-[2rem] border border-white/10 bg-[#0f1420] p-6 shadow-2xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-2xl font-semibold text-white">
                {title}
              </Dialog.Title>
              <Dialog.Description className="mt-2 text-sm leading-7 text-stone-300">
                {description}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button className="rounded-full border border-white/10 p-2 text-stone-300 transition hover:bg-white/10">
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>
          <div className="mt-6 space-y-3">
            {notes.map((note) => (
              <div
                key={note}
                className="rounded-2xl border border-white/8 bg-white/4 px-4 py-3 text-sm leading-7 text-stone-200"
              >
                {note}
              </div>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

/** Botão secundário leve usado em ações de navegação contextual. */
export function BotaoAcaoLeve({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-stone-200 transition hover:bg-white/10"
    >
      {label}
    </button>
  );
}

/** Card curto de destaque usado em visão geral e cobertura. */
export function CartaoDestaque({
  item,
}: {
  item: Snapshot["highlights"][number];
}) {
  return (
    <article className="rounded-[1.8rem] border border-white/8 bg-white/4 p-5 backdrop-blur-sm">
      <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
        {item.title}
      </p>
      <p className="mt-3 break-words text-2xl font-semibold tracking-[-0.04em] text-white">
        {item.value}
      </p>
      <p className="mt-3 text-sm leading-7 text-stone-300">{item.detail}</p>
    </article>
  );
}

/** Card de resumo de cobertura por fonte pública. */
export function CartaoCobertura({
  item,
}: {
  item: Snapshot["coverage"][number];
}) {
  return (
    <article className="rounded-[1.8rem] border border-white/8 bg-white/4 p-5 backdrop-blur-sm">
      <div className="flex flex-col gap-4">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
            {item.source}
          </p>
          <h3 className="mt-2 break-words text-xl font-semibold text-white">
            {item.total}
          </h3>
        </div>
        <div className="max-w-full self-start rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.2em] text-stone-300">
          {item.focus}
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm text-stone-300">
        <span>{item.records} Registros</span>
        <span>{item.agents} Agentes</span>
        <span>{item.suppliers} Fornecedores</span>
      </div>
    </article>
  );
}
