use serde::Serialize;

#[derive(Clone, Debug, Serialize)]
/// Resumo da cobertura detectada por fonte pública.
pub struct CoverageCard {
    pub source: String,
    pub total: String,
    pub records: usize,
    pub agents: usize,
    pub suppliers: usize,
    pub focus: String,
}
