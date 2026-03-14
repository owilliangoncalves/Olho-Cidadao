/**
 * Componentes estruturais do dashboard principal.
 *
 * Este arquivo concentra a moldura da experiência: barra superior, navegação
 * lateral e contêiner visual das seções.
 */
import type { ReactNode } from "react";

import {
  BarChart3,
  ChevronRight,
  Database,
  Eye,
  LayoutDashboard,
  Newspaper,
} from "lucide-react";

import {
  navegacaoPrimaria,
  socialConfig,
  type SecaoPrincipal,
} from "../../config/social";

/** Cabeçalho persistente da experiência pública. */
export function BarraSuperior({
  title,
  generatedAt,
}: {
  title: string;
  generatedAt: string;
}) {
  return (
    <header className="rounded-[2rem] border border-white/10 bg-[#0d1018]/76 px-4 py-4 shadow-[0_25px_80px_rgba(4,8,15,0.36)] backdrop-blur-xl md:px-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#f6b019,#d95e31_50%,#26b4a8)] shadow-[0_12px_35px_rgba(230,153,35,0.35)]">
            <Eye size={22} />
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-[0.3em] text-stone-500">
              Cidadão de olho
            </p>
            <h1 className="text-2xl font-semibold tracking-[-0.04em] text-white">
              {title}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Pilula text="Feed publico" tone="bg-white/6 text-stone-200" />
          <Pilula
            text={`Atualizado ${generatedAt}`}
            tone="bg-teal-400/10 text-teal-100"
          />
        </div>
      </div>
    </header>
  );
}

/** Navegação lateral com as áreas principais do produto. */
export function TrilhoNavegacao({
  activeSection,
  onChangeSection,
  generatedAt,
  years,
}: {
  activeSection: SecaoPrincipal;
  onChangeSection: (section: SecaoPrincipal) => void;
  generatedAt: string;
  years: number[];
}) {
  return (
    <aside className="lg:sticky lg:top-5 lg:self-start">
      <section className="rounded-[2.2rem] border border-white/10 bg-[#0d1018]/82 p-4 shadow-[0_25px_80px_rgba(4,8,15,0.34)] backdrop-blur-xl md:p-5">
        <p className="text-[11px] uppercase tracking-[0.26em] text-stone-500">
          {socialConfig.inspector.sectionLabel}
        </p>
        <p className="mt-3 text-sm leading-7 text-stone-300">
          {socialConfig.inspector.sectionHint}
        </p>

        <div className="mt-5 grid gap-2">
          {navegacaoPrimaria.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => onChangeSection(item.value)}
              className={`group rounded-[1.6rem] border px-4 py-4 text-left transition ${
                item.value === activeSection
                  ? "border-teal-300/25 bg-teal-300/10 shadow-[0_15px_40px_rgba(28,166,151,0.12)]"
                  : "border-white/8 bg-white/4 hover:bg-white/8"
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`mt-0.5 flex size-11 shrink-0 items-center justify-center rounded-2xl border ${
                    item.value === activeSection
                      ? "border-teal-300/20 bg-teal-300/14 text-teal-100"
                      : "border-white/10 bg-white/6 text-stone-300"
                  }`}
                >
                  {iconeSecao(item.value)}
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-stone-500">
                    {item.eyebrow}
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <p className="text-base font-semibold text-white">
                      {item.label}
                    </p>
                    <ChevronRight
                      size={14}
                      className={`transition ${
                        item.value === activeSection
                          ? "translate-x-0.5 text-teal-200"
                          : "text-stone-500 group-hover:text-stone-300"
                      }`}
                    />
                  </div>
                  <p className="mt-2 text-sm leading-6 text-stone-400">
                    {item.description}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="my-5 h-px bg-white/8" />

        <div className="rounded-[1.7rem] border border-white/8 bg-white/4 p-4">
          <p className="text-[11px] uppercase tracking-[0.24em] text-stone-500">
            Pulso do radar
          </p>
          <p className="mt-3 text-sm leading-7 text-stone-300">
            Ultima leitura pública em {generatedAt}. O recorte visivel hoje cobre{" "}
            {years.length} anos.
          </p>
        </div>
      </section>
    </aside>
  );
}

/** Moldura visual padrão para as seções principais da aplicação. */
export function MolduraSecao({
  eyebrow,
  title,
  description,
  actions,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[2.3rem] border border-white/10 bg-[#0d1018]/86 p-4 shadow-[0_40px_120px_rgba(4,8,15,0.45)] backdrop-blur-xl md:p-5">
      <div className="flex flex-col gap-4 border-b border-white/8 pb-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.26em] text-teal-300/80">
            {eyebrow}
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white md:text-4xl">
            {title}
          </h2>
          <p className="mt-3 text-sm leading-7 text-stone-300">{description}</p>
        </div>
        {actions ? (
          <div className="flex shrink-0 flex-wrap gap-3">{actions}</div>
        ) : null}
      </div>

      <div className="mt-4">{children}</div>
    </section>
  );
}

/** Badge simples usada para status e metadados curtos no topo. */
function Pilula({ text, tone }: { text: string; tone: string }) {
  return (
    <span className={`rounded-full px-4 py-2 text-xs uppercase tracking-[0.2em] ${tone}`}>
      {text}
    </span>
  );
}

/** Resolve o ícone da seção ativa na navegação principal. */
function iconeSecao(section: SecaoPrincipal) {
  switch (section) {
    case "overview":
      return <LayoutDashboard size={18} />;
    case "feed":
      return <Newspaper size={18} />;
    case "rankings":
      return <BarChart3 size={18} />;
    case "coverage":
      return <Database size={18} />;
    default:
      return <Eye size={18} />;
  }
}
