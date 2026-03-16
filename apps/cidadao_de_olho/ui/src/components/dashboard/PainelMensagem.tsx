import { RefreshCcw } from "lucide-react";

import type { PainelMensagemModelo } from "../../types";
import { PainelEstado } from "./PainelEstado";
import { TextoEstado } from "./TextoEstado";

/** Painel visual generico para mensagens de carregamento, erro e espera. */
export function PainelMensagem({
  sobrelinha,
  titulo,
  descricao,
  visual,
  acao,
}: PainelMensagemModelo) {
  return (
    <PainelEstado classNamePainel={visual.classNamePainel}>
      <TextoEstado
        texto={sobrelinha}
        className={visual.classNameSobrelinha}
        reservaClassName={visual.classNameReservaSobrelinha}
      />
      <TextoEstado
        texto={titulo}
        titulo
        className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-white"
        reservaClassName={visual.classNameReservaTitulo}
      />
      <TextoEstado
        texto={descricao}
        className={visual.classNameDescricao}
        reservaClassName={visual.classNameReservaDescricao}
      />

      {acao ? (
        <button
          type="button"
          onClick={acao.aoClicar}
          aria-label={acao.rotuloAria}
          className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-white transition hover:bg-white/15"
        >
          {acao.mostrarIconeAtualizar ? <RefreshCcw size={16} /> : null}
          {acao.rotulo ? (
            <span>{acao.rotulo}</span>
          ) : (
            <span
              aria-hidden="true"
              className="h-4 w-24 rounded-full bg-white/10"
            />
          )}
        </button>
      ) : null}
    </PainelEstado>
  );
}
