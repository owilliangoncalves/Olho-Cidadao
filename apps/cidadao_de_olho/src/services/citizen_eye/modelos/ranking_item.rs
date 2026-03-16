use serde::Serialize;

#[derive(Clone, Debug, Serialize)]
/// Agrupamento dos rankings usados na navegação principal da interface.
pub struct RankingGroups {
    pub fornecedores: Vec<RankingItem>,
    pub agentes: Vec<RankingItem>,
    pub tipos_despesa: Vec<RankingItem>,
    pub ufs: Vec<RankingItem>,
}

#[derive(Clone, Debug, Serialize)]
/// Item unitário de ranking.
pub struct RankingItem {
    pub label: String,
    pub value: String,
    pub extra: Option<String>,
    pub sources: Vec<String>,
    pub share: f64,
}
