import { runtimeConfig } from "../config/runtime";

/** Constrói a URL da API pública a partir do runtime ativo. */
export function montarUrlApiPublica(caminho: string): URL {
  return new URL(`${runtimeConfig.apiBase}/${caminho}`, window.location.origin);
}
