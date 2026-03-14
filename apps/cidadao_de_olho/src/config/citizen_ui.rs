//! Configuração de branding e copy da interface pública.
//!
//! O frontend recebe parte importante dos textos pelo backend para evitar copy
//! hardcoded na camada React e para permitir ajustes editoriais sem tocar na
//! lógica de renderização.

use std::path::Path;

use anyhow::Result;
use serde::Deserialize;

use super::carregador::carregar_config_toml;

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize)]
/// Configuração raiz da experiência visual entregue ao usuário.
pub struct CitizenUiConfig {
    pub branding: BrandingConfig,
    pub copy: CopyConfig,
}

#[derive(Clone, Debug, Deserialize)]
/// Elementos estáveis de identidade visual e posicionamento do app.
pub struct BrandingConfig {
    pub title: String,
    pub eyebrow: String,
    pub headline: String,
    pub subheadline: String,
    pub refresh_label: String,
}

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

impl CitizenUiConfig {
    /// Carrega a configuração de interface do app.
    pub fn load() -> Result<Self> {
        let path = Path::new(MANIFEST_DIR)
            .join("config")
            .join("citizen_ui.toml");
        carregar_config_toml(&path)
    }
}
