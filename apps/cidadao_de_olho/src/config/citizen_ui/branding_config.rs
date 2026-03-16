use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
/// Elementos estáveis de identidade visual e posicionamento do app.
pub struct BrandingConfig {
    pub title: String,
    pub eyebrow: String,
    pub headline: String,
    pub subheadline: String,
    pub refresh_label: String,
}
