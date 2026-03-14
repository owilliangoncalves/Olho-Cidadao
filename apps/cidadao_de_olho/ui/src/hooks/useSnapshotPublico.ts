/**
 * Hook de carregamento do snapshot público.
 *
 * Encapsula fetch, estados de carregamento/erro e o refresh manual para que
 * a raiz da aplicação não acumule lógica de rede.
 */
import { useEffect, useState } from "react";

import { runtimeConfig } from "../config/runtime";
import type { Snapshot } from "../types";

export type EstadoBusca = "idle" | "loading" | "ready" | "error";

/** Carrega e expõe o snapshot consumido pela interface pública. */
export function useSnapshotPublico() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [status, setStatus] = useState<EstadoBusca>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    void carregarSnapshot(false);
  }, []);

  /**
   * Recarrega o snapshot da API.
   *
   * Quando `forceRefresh` é verdadeiro, a query string pede ao backend para
   * ignorar o cache em memória.
   */
  async function carregarSnapshot(forceRefresh: boolean) {
    setStatus((current) => (current === "ready" ? current : "loading"));
    setRefreshing(forceRefresh);
    setErrorMessage("");

    try {
      const url = new URL(
        `${runtimeConfig.apiBase}/snapshot`,
        window.location.origin,
      );
      if (forceRefresh) {
        url.searchParams.set("refresh", "1");
      }

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error("Nao foi possivel carregar o radar publico.");
      }

      const data = (await response.json()) as Snapshot;
      setSnapshot(data);
      setStatus("ready");
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        error instanceof Error ? error.message : "Falha inesperada.",
      );
    } finally {
      setRefreshing(false);
    }
  }

  return {
    snapshot,
    status,
    errorMessage,
    refreshing,
    carregarSnapshot,
  };
}
