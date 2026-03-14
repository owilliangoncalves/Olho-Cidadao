/**
 * Configuração de runtime do frontend.
 *
 * Este arquivo concentra apenas o que varia por ambiente de execução do
 * bundle, hoje restrito à base da API pública.
 */
export const runtimeConfig = {
  apiBase: import.meta.env.VITE_CITIZEN_API_BASE ?? "/api",
};
