use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
/// Textos operacionais exibidos na interface pública.
pub struct CopyConfig {
    pub feed_title: String,
    pub feed_subtitle: String,
    pub search_label: String,
    pub search_placeholder: String,
    pub guide_title: String,
    pub guide_body: String,
    pub methodology_title: String,
    pub methodology: Vec<String>,
    pub empty_feed_message: String,
    pub coverage_title: String,
    pub highlights_title: String,
    pub suppliers_title: String,
    pub agents_title: String,
    pub expenses_title: String,
}
