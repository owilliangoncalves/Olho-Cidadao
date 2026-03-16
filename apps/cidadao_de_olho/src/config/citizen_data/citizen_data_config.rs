use std::path::{Path, PathBuf};

use anyhow::Result;
use serde::Deserialize;

use crate::config::carregador::{carregar_config_toml, resolver_caminho_config_ambiente};

use super::{resolve_relative::resolve_relative, CitizenDataLimits, CitizenDataPaths};

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize)]
/// Configuração raiz dos dados consumidos pelo app.
pub struct CitizenDataConfig {
    pub paths: CitizenDataPaths,
    pub limits: CitizenDataLimits,
}

impl CitizenDataConfig {
    /// Carrega a configuração de dados adequada ao ambiente atual.
    pub fn load() -> Result<Self> {
        let path = resolver_caminho_config_ambiente(Path::new(MANIFEST_DIR), "citizen_data");
        carregar_config_toml(&path)
    }

    #[must_use]
    pub fn project_root(&self) -> PathBuf {
        resolve_relative(Path::new(MANIFEST_DIR), &self.paths.project_root)
    }

    /// Caminho absoluto do CSV consolidado da Câmara.
    #[must_use]
    pub fn camara_csv_path(&self) -> PathBuf {
        resolve_relative(&self.project_root(), &self.paths.camara_csv)
    }

    /// Caminho absoluto do diretório com os JSONs do Senado.
    #[must_use]
    pub fn senado_dir_path(&self) -> PathBuf {
        resolve_relative(&self.project_root(), &self.paths.senado_dir)
    }

    /// Caminho absoluto da dimensão JSONL de fornecedores.
    #[must_use]
    pub fn suppliers_jsonl_path(&self) -> PathBuf {
        resolve_relative(&self.project_root(), &self.paths.suppliers_jsonl)
    }
}
