import type { PainelHeroiProps } from "../../types";

/** Painel hero com headline principal e métricas de contexto. */
export function PainelHeroi({
  eyebrow,
  headline,
  subheadline,
  metrics,
  actions,
}: PainelHeroiProps) {
  return (
    <section className="relative overflow-hidden rounded-[2.3rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(246,176,25,0.22),_transparent_22%),radial-gradient(circle_at_bottom_right,_rgba(31,183,164,0.18),_transparent_28%),linear-gradient(135deg,_rgba(11,14,22,0.9),_rgba(21,26,38,0.94))] p-5 shadow-[0_32px_96px_rgba(4,8,15,0.42)] md:p-6 xl:p-7">
      <div className="absolute inset-y-0 right-[-120px] w-[320px] rounded-full bg-teal-300/10 blur-3xl" />
      <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:items-end">
        <div>
          <p className="text-[11px] uppercase tracking-[0.3em] text-amber-200/85">
            {eyebrow}
          </p>
          <h2 className="mt-3 max-w-4xl text-4xl font-semibold tracking-[-0.06em] text-white md:text-5xl xl:text-[4rem] xl:leading-[0.95]">
            {headline}
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-8 text-stone-300 md:text-lg">
            {subheadline}
          </p>
          {actions ? (
            <div className="mt-6 flex flex-wrap gap-3">{actions}</div>
          ) : null}
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {metrics.map((metric) => (
            <article
              key={metric.id}
              className={`rounded-[1.7rem] border p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] ${metric.className}`}
            >
              <p className="text-[11px] uppercase tracking-[0.24em] text-stone-300/80">
                {metric.label}
              </p>
              <p className="mt-3 break-words text-[2rem] font-semibold tracking-[-0.04em] text-white">
                {metric.value}
              </p>
              <p className="mt-2 text-sm leading-6 text-stone-300">
                {metric.detail}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
