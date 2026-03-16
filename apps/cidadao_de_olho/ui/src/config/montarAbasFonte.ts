import type { ItemAbaFonte, TextosConfig } from "../types";

/** Abas disponíveis para filtrar o feed por fonte. */
export function montarAbasFonte(textos: TextosConfig): ItemAbaFonte[] {
  return [
    { value: "all", label: textos.feed.aba_todas },
    { value: "Camara", label: textos.feed.aba_camara },
    { value: "Senado", label: textos.feed.aba_senado },
  ];
}
