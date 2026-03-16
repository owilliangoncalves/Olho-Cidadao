import type { MolduraSecaoProps } from "../../types";

/** Moldura visual padrão para as seções principais da aplicação. */
export function MolduraSecao({
  eyebrow,
  title,
  description,
  actions,
  children,
}: MolduraSecaoProps) {
  return (
    <section className="rounded-[2.1rem] border border-white/8 bg-[#0d1018]/80 p-5 shadow-[0_32px_96px_rgba(4,8,15,0.38)] backdrop-blur-xl md:p-6">
      <div className="flex flex-col gap-4 border-b border-white/8 pb-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.26em] text-teal-300/80">
            {eyebrow}
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white md:text-3xl">
            {title}
          </h2>
          <p className="mt-3 text-sm leading-7 text-stone-300">{description}</p>
        </div>
        {actions ? (
          <div className="flex shrink-0 flex-wrap gap-3">{actions}</div>
        ) : null}
      </div>

      <div className="mt-5">{children}</div>
    </section>
  );
}
