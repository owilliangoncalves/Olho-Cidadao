import type { NotaPainelModelo } from "../types";

/** Limita e identifica notas curtas para os painéis laterais e modais. */
export function montarNotasPainel(
  notas: string[],
  limite = notas.length,
): NotaPainelModelo[] {
  return notas.slice(0, limite).map((nota, indice) => ({
    id: `${indice}-${nota}`,
    texto: nota,
  }));
}
