import * as Separator from "@radix-ui/react-separator";
import { Sparkles } from "lucide-react";

import type { TrilhoGuiaProps } from "../../types";

/** Bloco lateral com explicação rápida e notas metodológicas curtas. */
export function TrilhoGuia({
  eyebrow,
  title,
  body,
  notes,
}: TrilhoGuiaProps) {
  return (
    <section className="rounded-[2rem] border border-white/8 bg-[#101522]/78 p-5 shadow-[0_20px_60px_rgba(4,8,15,0.26)] backdrop-blur-xl">
      <p className="text-[11px] uppercase tracking-[0.26em] text-stone-500">
        {eyebrow}
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-white">
        {title}
      </h2>
      <p className="mt-4 text-sm leading-7 text-stone-300">{body}</p>

      <Separator.Root className="my-5 h-px bg-white/8" decorative />

      <div className="space-y-3">
        {notes.map((note) => (
          <div
            key={note.id}
            className="rounded-[1.4rem] border border-white/8 bg-[#0a0d15]/72 p-4"
          >
            <div className="flex items-start gap-3">
              <Sparkles size={16} className="mt-1 shrink-0 text-amber-300" />
              <p className="text-sm leading-6 text-stone-200">{note.texto}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
