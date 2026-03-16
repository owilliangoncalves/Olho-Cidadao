import type { Snapshot } from "../types";

import { montarMensagemErroHttpSnapshot } from "./montarMensagemErroHttpSnapshot";
import { montarUrlApiPublica } from "./montarUrlApiPublica";

/** Busca o snapshot principal consumido pela interface pública. */
export async function buscarSnapshotPublico(
  forceRefresh: boolean,
): Promise<Snapshot> {
  const url = montarUrlApiPublica("snapshot");
  if (forceRefresh) {
    url.searchParams.set("refresh", "1");
  }

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(montarMensagemErroHttpSnapshot(response.status));
  }

  return (await response.json()) as Snapshot;
}
