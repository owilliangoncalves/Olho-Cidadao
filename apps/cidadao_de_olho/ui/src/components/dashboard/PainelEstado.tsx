import type { ReactNode } from "react";

/** Moldura visual compartilhada pelas telas de estado do dashboard. */
export function PainelEstado({
  classNamePainel,
  children,
}: {
  classNamePainel: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0d15] px-4">
      <div className={`rounded-[2rem] px-8 py-7 shadow-2xl ${classNamePainel}`}>
        {children}
      </div>
    </div>
  );
}
