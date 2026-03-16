/** Substitui placeholders do tipo `{nome}` em templates curtos. */
export function interpolarTexto(
  template: string,
  valores: Record<string, string | number>,
) {
  return template.replace(/\{(\w+)\}/g, (_trecho: string, chave: string) =>
    String(valores[chave] ?? ""),
  );
}
