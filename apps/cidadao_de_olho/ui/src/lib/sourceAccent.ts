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
