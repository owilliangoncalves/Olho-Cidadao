import type { Snapshot, UiPayload } from "./contratosPublicos";

export type EstadoBusca = "idle" | "loading" | "ready" | "error";

export type UseSnapshotPublicoResultado = {
  snapshot: Snapshot | null;
  uiPublica: UiPayload | null;
  status: EstadoBusca;
  errorMessage: string;
  refreshing: boolean;
  carregarSnapshot: (forceRefresh: boolean) => Promise<void>;
};
