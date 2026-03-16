use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
/// Limites de exposição para o contrato público do app.
pub struct CitizenDataLimits {
    pub max_feed_items: usize,
    pub max_ranking_items: usize,
}
