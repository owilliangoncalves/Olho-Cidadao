/**
 * Funções de formatação e mapeamento visual do frontend.
 */

/** Formata a data de geração do snapshot para exibição em pt-BR. */
export function formatGeneratedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

/** Escolhe o gradiente visual de acordo com a fonte pública do card. */
export function sourceAccent(source: string): string {
  if (source === "Camara") {
    return "from-amber-400/70 via-orange-300/25 to-transparent";
  }
  if (source === "Senado") {
    return "from-emerald-400/70 via-teal-300/25 to-transparent";
  }
  return "from-sky-400/70 via-cyan-300/20 to-transparent";
}

/** Resolve a paleta visual das métricas do hero com base no tom configurado. */
export function metricToneClass(tone: string): string {
  const palette: Record<string, string> = {
    amber:
      "border-amber-400/30 bg-amber-300/10 text-amber-100 ring-1 ring-amber-400/15",
    cyan:
      "border-cyan-400/30 bg-cyan-300/10 text-cyan-100 ring-1 ring-cyan-400/15",
    green:
      "border-emerald-400/30 bg-emerald-300/10 text-emerald-100 ring-1 ring-emerald-400/15",
    magenta:
      "border-fuchsia-400/30 bg-fuchsia-300/10 text-fuchsia-100 ring-1 ring-fuchsia-400/15",
  };

  return (
    palette[tone] ??
    "border-white/15 bg-white/8 text-stone-100 ring-1 ring-white/10"
  );
}
