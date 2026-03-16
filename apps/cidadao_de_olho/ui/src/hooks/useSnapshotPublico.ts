/**
 * Hook de carregamento do snapshot público.
 *
 * Encapsula fetch, estados de carregamento/erro e o refresh manual para que
 * a raiz da aplicação não acumule lógica de rede.
 */
import { useEffect, useState } from "react";

import type {
  EstadoBusca,
  Snapshot,
  UiPayload,
  UseSnapshotPublicoResultado,
} from "../types";
import { buscarInterfacePublica } from "../lib/buscarInterfacePublica";
import { buscarSnapshotPublico } from "../lib/buscarSnapshotPublico";

/** Carrega e expõe o snapshot consumido pela interface pública. */
export function useSnapshotPublico(): UseSnapshotPublicoResultado {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [uiPublica, setUiPublica] = useState<UiPayload | null>(null);
  const [status, setStatus] = useState<EstadoBusca>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    void carregarInterfacePublica();
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
      const data = await buscarSnapshotPublico(forceRefresh);
      setSnapshot(data);
      setStatus("ready");
    } catch (error) {
      setStatus("error");
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Falha inesperada ao carregar o radar publico.",
      );
    } finally {
      setRefreshing(false);
    }
  }

  async function carregarInterfacePublica() {
    try {
      const data = await buscarInterfacePublica();
      if (!data) {
        return;
      }

      setUiPublica(data);
    } catch {
      // A interface usa fallback local se a configuracao textual ainda nao
      // estiver disponivel.
    }
  }

  return {
    snapshot,
    uiPublica,
    status,
    errorMessage,
    refreshing,
    carregarSnapshot,
  };
}
