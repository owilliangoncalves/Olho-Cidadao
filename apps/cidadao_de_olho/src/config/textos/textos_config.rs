use std::path::Path;

use anyhow::Result;
use serde::{Deserialize, Serialize};

use crate::config::carregador::{caminho_config, carregar_config_toml};

use super::{
    TextosBarraSuperior, TextosCobertura, TextosCompartilhados, TextosEstados, TextosFeed,
    TextosGlossario, TextosRankings, TextosVisaoGeral,
};

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosConfig {
    pub barra_superior: TextosBarraSuperior,
    pub estados: TextosEstados,
    pub compartilhado: TextosCompartilhados,
    pub visao_geral: TextosVisaoGeral,
    pub feed: TextosFeed,
    pub rankings: TextosRankings,
    pub cobertura: TextosCobertura,
    pub glossario: TextosGlossario,
}

impl TextosConfig {
    /// Carrega os textos centralizados da interface.
    pub fn load() -> Result<Self> {
        let path = caminho_config(Path::new(MANIFEST_DIR), "textos.toml");
        carregar_config_toml(&path)
    }
}
