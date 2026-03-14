/**
 * Raiz da aplicação React.
 *
 * A responsabilidade aqui é apenas coordenar estado de navegação, compor as
 * seções e conectar o hook de carregamento do snapshot.
 */
import { useMemo, useState } from "react";

import { EstadoCarregando, EstadoErro } from "./components/dashboard/Estados";
import { BarraSuperior, TrilhoNavegacao } from "./components/dashboard/Estrutura";
import {
  type AbaCobertura,
  type AbaRanking,
  type FiltroFonte,
  type SecaoPrincipal,
} from "./config/social";
import { useSnapshotPublico } from "./hooks/useSnapshotPublico";
import { filtrarFeed } from "./lib/feed";
import { formatGeneratedAt } from "./lib/format";
import { SecaoCobertura } from "./sections/SecaoCobertura";
import { SecaoFeed } from "./sections/SecaoFeed";
import { SecaoRankings } from "./sections/SecaoRankings";
import { SecaoVisaoGeral } from "./sections/SecaoVisaoGeral";

/** Composição principal do dashboard público. */
export function App() {
  const {
    snapshot,
    status,
    errorMessage,
    refreshing,
    carregarSnapshot,
  } = useSnapshotPublico();

  const [query, setQuery] = useState("");
  const [source, setSource] = useState<FiltroFonte>("all");
  const [secaoPrincipal, setSecaoPrincipal] =
    useState<SecaoPrincipal>("overview");
  const [abaRanking, setAbaRanking] = useState<AbaRanking>("fornecedores");
  const [abaCobertura, setAbaCobertura] = useState<AbaCobertura>("fontes");

  const feedFiltrado = useMemo(
    () => filtrarFeed(snapshot?.feed ?? [], query, source),
    [query, snapshot, source],
  );

  if (status === "loading" && !snapshot) {
    return <EstadoCarregando />;
  }

  if (status === "error" && !snapshot) {
    return (
      <EstadoErro
        message={errorMessage}
        onRetry={() => void carregarSnapshot(true)}
      />
    );
  }

  if (!snapshot) {
    return null;
  }

  const geradoEm = formatGeneratedAt(snapshot.meta.generated_at);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(255,186,69,0.18),_transparent_22%),radial-gradient(circle_at_top_right,_rgba(24,177,171,0.17),_transparent_28%),linear-gradient(180deg,_#090b11_0%,_#121621_48%,_#171b29_100%)] text-stone-100">
      <div className="mx-auto flex min-h-screen max-w-[1700px] flex-col px-4 pb-8 pt-5 md:px-6 xl:px-8">
        <BarraSuperior title={snapshot.meta.title} generatedAt={geradoEm} />

        <div className="mt-5 grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
          <TrilhoNavegacao
            activeSection={secaoPrincipal}
            generatedAt={geradoEm}
            years={snapshot.meta.coverage_years}
            onChangeSection={setSecaoPrincipal}
          />

          <main className="min-w-0 space-y-5">
            {secaoPrincipal === "overview" ? (
              <SecaoVisaoGeral
                generatedAt={geradoEm}
                snapshot={snapshot}
                onJumpToCoverage={() => setSecaoPrincipal("coverage")}
                onJumpToFeed={() => setSecaoPrincipal("feed")}
              />
            ) : null}

            {secaoPrincipal === "feed" ? (
              <SecaoFeed
                snapshot={snapshot}
                generatedAt={geradoEm}
                source={source}
                query={query}
                refreshing={refreshing}
                filteredFeed={feedFiltrado}
                onQueryChange={setQuery}
                onRefresh={() => void carregarSnapshot(true)}
                onSourceChange={setSource}
              />
            ) : null}

            {secaoPrincipal === "rankings" ? (
              <SecaoRankings
                snapshot={snapshot}
                activeTab={abaRanking}
                onChangeTab={setAbaRanking}
              />
            ) : null}

            {secaoPrincipal === "coverage" ? (
              <SecaoCobertura
                snapshot={snapshot}
                activeTab={abaCobertura}
                onChangeTab={setAbaCobertura}
              />
            ) : null}
          </main>
        </div>
      </div>
    </div>
  );
}
