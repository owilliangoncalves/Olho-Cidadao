use serde::Serialize;

#[derive(Clone, Debug, Serialize)]
/// Card unitário do feed cívico.
pub struct FeedCard {
    pub source: String,
    pub period: String,
    pub headline: String,
    pub body: String,
    pub actor: String,
    pub actor_meta: String,
    pub supplier: String,
    pub supplier_doc: Option<String>,
    pub amount: String,
    pub expense_type: String,
    pub tags: Vec<String>,
}
