import type { ItemAbaCobertura, TextosConfig } from "../types";

/** Submenus da área de cobertura e metodologia. */
export function montarAbasCobertura(textos: TextosConfig): ItemAbaCobertura[] {
  return [
    { value: "fontes", label: textos.cobertura.aba_fontes },
    { value: "destaques", label: textos.cobertura.aba_destaques },
    { value: "notas", label: textos.cobertura.aba_notas },
  ];
}
