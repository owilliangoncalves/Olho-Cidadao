use serde::Serialize;

use crate::config::{citizen_ui::CopyConfig, textos::TextosConfig};

#[derive(Clone, Debug, Serialize)]
/// Textos de interface enviados pelo backend para evitar copy hardcoded no frontend.
pub struct UiPayload {
    pub eyebrow: String,
    pub refresh_label: String,
    pub feed_title: String,
    pub feed_subtitle: String,
    pub search_label: String,
    pub search_placeholder: String,
    pub guide_title: String,
    pub guide_body: String,
    pub methodology_title: String,
    pub empty_feed_message: String,
    pub coverage_title: String,
    pub highlights_title: String,
    pub suppliers_title: String,
    pub agents_title: String,
    pub expenses_title: String,
    pub textos: TextosConfig,
}

impl UiPayload {
    /// Converte a configuração de copy em payload pronto para a interface.
    #[must_use]
    pub fn from_configuracoes(
        copy: &CopyConfig,
        refresh_label: &str,
        textos: &TextosConfig,
    ) -> Self {
        Self {
            eyebrow: "Feed civico".to_string(),
            refresh_label: refresh_label.to_string(),
            feed_title: copy.feed_title.clone(),
            feed_subtitle: copy.feed_subtitle.clone(),
            search_label: copy.search_label.clone(),
            search_placeholder: copy.search_placeholder.clone(),
            guide_title: copy.guide_title.clone(),
            guide_body: copy.guide_body.clone(),
            methodology_title: copy.methodology_title.clone(),
            empty_feed_message: copy.empty_feed_message.clone(),
            coverage_title: copy.coverage_title.clone(),
            highlights_title: copy.highlights_title.clone(),
            suppliers_title: copy.suppliers_title.clone(),
            agents_title: copy.agents_title.clone(),
            expenses_title: copy.expenses_title.clone(),
            textos: textos.clone(),
        }
    }
}
