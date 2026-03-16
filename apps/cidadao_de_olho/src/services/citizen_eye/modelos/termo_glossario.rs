use serde::Serialize;

use crate::config::glossario::TermoGlossarioConfig;

#[derive(Clone, Debug, Serialize)]
/// Termo do glossario acessivel exibido na interface.
pub struct TermoGlossario {
    pub termo: String,
    pub grupo: String,
    pub definicao: String,
    pub contexto: String,
    pub relacionados: Vec<String>,
}

impl TermoGlossario {
    /// Converte a configuracao editorial em payload publico.
    #[must_use]
    pub fn from_config(config: &TermoGlossarioConfig) -> Self {
        Self::from(config)
    }
}

impl From<&TermoGlossarioConfig> for TermoGlossario {
    fn from(config: &TermoGlossarioConfig) -> Self {
        Self {
            termo: config.termo.clone(),
            grupo: config.grupo.clone(),
            definicao: config.definicao.clone(),
            contexto: config.contexto.clone(),
            relacionados: config.relacionados.clone(),
        }
    }
}
