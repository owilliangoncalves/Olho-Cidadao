import * as Dialog from "@radix-ui/react-dialog";
import { ShieldAlert, X } from "lucide-react";

import type { BotaoMetodologiaProps } from "../../types";

/** Botão que abre o modal de metodologia do produto. */
export function BotaoMetodologia({
  triggerLabel,
  title,
  description,
  notes,
}: BotaoMetodologiaProps) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-stone-200 transition hover:bg-white/10">
          <ShieldAlert size={16} />
          {triggerLabel}
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
                key={note.id}
                className="rounded-2xl border border-white/8 bg-white/4 px-4 py-3 text-sm leading-7 text-stone-200"
              >
                {note.texto}
              </div>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
