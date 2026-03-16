import type { GrupoGlossario, TextosGlossario } from "../types";

/** Resolve a descrição curta de cada grupo do glossário. */
export function descricaoGrupoGlossario(
  grupo: GrupoGlossario,
  textos: TextosGlossario,
) {
  switch (grupo) {
    case "Leitura do dado":
      return textos.descricao_grupo_leitura_do_dado;
    case "Interface":
      return textos.descricao_grupo_interface;
    case "Metodo":
      return textos.descricao_grupo_metodo;
    default:
      return "";
  }
}
