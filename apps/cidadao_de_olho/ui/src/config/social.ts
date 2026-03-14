/**
 * Configuração editorial da navegação social do app.
 *
 * Este arquivo existe para concentrar rótulos, menus e organização da
 * experiência sem espalhar copy hardcoded pelos componentes React.
 */
export type SecaoPrincipal = "overview" | "feed" | "rankings" | "coverage";
export type AbaRanking = "fornecedores" | "agentes" | "tipos" | "ufs";
export type AbaCobertura = "fontes" | "destaques" | "notas";
export type FiltroFonte = "all" | "Camara" | "Senado";

/** Configuração-base de navegação e textos auxiliares da experiência. */
export const socialConfig = {
  primaryNav: [
    {
      value: "overview",
      label: "Visao geral",
      eyebrow: "Entrada",
      description: "Panorama, hero e contexto rapido.",
    },
    {
      value: "feed",
      label: "Timeline",
      eyebrow: "Leitura social",
      description: "Cards de gasto publico em formato de feed.",
    },
    {
      value: "rankings",
      label: "Rankings",
      eyebrow: "Comparativos",
      description: "Fornecedores, agentes, tipos e UFs em foco.",
    },
    {
      value: "coverage",
      label: "Cobertura",
      eyebrow: "Transparencia",
      description: "Fontes, destaques e notas de metodologia.",
    },
  ],
  sourceTabs: [
    { value: "all", label: "Tudo" },
    { value: "Camara", label: "Camara" },
    { value: "Senado", label: "Senado" },
  ],
  rankingTabs: [
    { value: "fornecedores", label: "Fornecedores" },
    { value: "agentes", label: "Agentes" },
    { value: "tipos", label: "Tipos" },
    { value: "ufs", label: "UFs" },
  ],
  coverageTabs: [
    { value: "fontes", label: "Fontes" },
    { value: "destaques", label: "Destaques" },
    { value: "notas", label: "Notas" },
  ],
  inspector: {
    liveLabel: "Ao vivo",
    transparentLabel: "Transparencia em formato de feed",
    rankingLabel: "Quem mais aparece agora",
    highlightLabel: "O que merece olhar hoje",
    sectionLabel: "Explorar",
    sectionHint: "Escolha uma area para reduzir ruído e navegar por contexto.",
    methodologyTrigger: "Como esse radar funciona",
    methodologyHint:
      "Os dados sao lidos dos artefatos do ETL e apresentados como uma timeline publica com contexto.",
  },
};

/** Navegação principal já tipada para consumo pelos componentes. */
export const navegacaoPrimaria = socialConfig.primaryNav as Array<{
  value: SecaoPrincipal;
  label: string;
  eyebrow: string;
  description: string;
}>;

/** Abas disponíveis para filtrar a timeline por fonte. */
export const abasFonte = socialConfig.sourceTabs as Array<{
  value: FiltroFonte;
  label: string;
}>;

/** Submenus da área de rankings. */
export const abasRanking = socialConfig.rankingTabs as Array<{
  value: AbaRanking;
  label: string;
}>;

/** Submenus da área de cobertura e metodologia. */
export const abasCobertura = socialConfig.coverageTabs as Array<{
  value: AbaCobertura;
  label: string;
}>;
