import type { GrupoGlossario, TermoGlossario } from "../types";

const ordemGrupos: GrupoGlossario[] = [
  "Leitura do dado",
  "Interface",
  "Metodo",
];

/** Filtra e agrupa os termos do glossário para renderização. */
export function montarModeloSecaoGlossario(
  termos: TermoGlossario[],
  queryNormalizada: string,
) {
  const termosFiltrados = termos.filter((item) => {
    if (!queryNormalizada) {
      return true;
    }

    const alvo = [
      item.termo,
      item.definicao,
      item.contexto,
      item.grupo,
      item.relacionados.join(" "),
    ]
      .join(" ")
      .toLowerCase();

    return alvo.includes(queryNormalizada);
  });

  const gruposComResultados = ordemGrupos
    .map((grupo) => ({
      grupo,
      itens: termosFiltrados.filter((item) => item.grupo === grupo),
    }))
    .filter((item) => item.itens.length > 0);

  return {
    termosFiltrados,
    gruposComResultados,
  };
}
