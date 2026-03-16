use std::path::Path;

use anyhow::Result;
use serde::Deserialize;

use crate::config::carregador::{caminho_config, carregar_config_toml};

use super::{BrandingConfig, CopyConfig};

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize)]
/// Configuração raiz da experiência visual entregue ao usuário.
pub struct CitizenUiConfig {
    pub branding: BrandingConfig,
    pub copy: CopyConfig,
}

impl CitizenUiConfig {
    /// Carrega a configuração de interface do app.
    pub fn load() -> Result<Self> {
        let path = caminho_config(Path::new(MANIFEST_DIR), "citizen_ui.toml");
        carregar_config_toml(&path)
    }
}
