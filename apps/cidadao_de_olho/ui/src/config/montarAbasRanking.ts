import type { ItemAbaRanking, TextosConfig } from "../types";

/** Submenus da área de rankings. */
export function montarAbasRanking(textos: TextosConfig): ItemAbaRanking[] {
  return [
    { value: "fornecedores", label: textos.rankings.aba_fornecedores },
    { value: "agentes", label: textos.rankings.aba_agentes },
    { value: "tipos", label: textos.rankings.aba_tipos },
    { value: "ufs", label: textos.rankings.aba_ufs },
  ];
}
