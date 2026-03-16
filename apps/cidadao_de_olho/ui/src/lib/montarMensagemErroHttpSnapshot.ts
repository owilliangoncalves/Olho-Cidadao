import { runtimeConfig } from "../config/runtime";

/** Traduz falhas HTTP do snapshot público em mensagens de leitura simples. */
export function montarMensagemErroHttpSnapshot(status: number): string {
  if (
    import.meta.env.DEV &&
    status === 404 &&
    runtimeConfig.apiBase === "/api"
  ) {
    return "A API /api/snapshot nao respondeu no modo desenvolvimento. Suba o backend com `uv run python main.py servir-cidadao-de-olho` e recarregue a pagina.";
  }

  return `Nao foi possivel carregar o radar publico (HTTP ${status}).`;
}
