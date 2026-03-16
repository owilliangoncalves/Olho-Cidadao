import type { UiPayload } from "../types";

import { montarUrlApiPublica } from "./montarUrlApiPublica";

/** Busca os textos e rótulos públicos do backend, quando disponíveis. */
export async function buscarInterfacePublica(): Promise<UiPayload | null> {
  const response = await fetch(montarUrlApiPublica("interface").toString());
  if (!response.ok) {
    return null;
  }

  return (await response.json()) as UiPayload;
}
