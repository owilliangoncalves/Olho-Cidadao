//! Configuracao editorial do glossario acessivel da interface publica.
//!
//! O objetivo deste arquivo e manter o vocabulario da experiencia fora da
//! camada React, permitindo evolucao editorial sem espalhar texto hardcoded.

use std::path::Path;

use anyhow::Result;
use serde::Deserialize;

use super::carregador::carregar_config_toml;

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize)]
/// Configuracao raiz do glossario da interface publica.
pub struct GlossarioConfig {
    pub termos: Vec<TermoGlossarioConfig>,
}

#[derive(Clone, Debug, Deserialize)]
/// Termo unitario exibido na pagina de glossario.
pub struct TermoGlossarioConfig {
    pub termo: String,
    pub grupo: String,
    pub definicao: String,
    pub contexto: String,
    pub relacionados: Vec<String>,
}

impl GlossarioConfig {
    /// Carrega o glossario editorial do app.
    pub fn load() -> Result<Self> {
        let path = Path::new(MANIFEST_DIR).join("config").join("glossario.toml");
        carregar_config_toml(&path)
    }
}
