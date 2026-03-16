//! Configuração de leitura dos artefatos de dados do `Olho Cidadão`.
//!
//! Este módulo resolve os caminhos físicos usados pelo backend para localizar
//! os arquivos produzidos pelo ETL. A ideia é manter a camada de serviço
//! desacoplada de caminhos hardcoded e de diferenças entre ambientes.

use std::path::{Path, PathBuf};

use anyhow::Result;
use serde::Deserialize;

use super::carregador::{carregar_config_toml, resolver_caminho_config_ambiente};

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize)]
/// Configuração raiz dos dados consumidos pelo app.
pub struct CitizenDataConfig {
    pub paths: CitizenDataPaths,
    pub limits: CitizenDataLimits,
}

#[derive(Clone, Debug, Deserialize)]
/// Caminhos dos artefatos usados para montar o snapshot público.
pub struct CitizenDataPaths {
    pub project_root: String,
    pub camara_csv: String,
    pub senado_dir: String,
    pub suppliers_jsonl: String,
}

#[derive(Clone, Debug, Deserialize)]
/// Limites de exposição para o contrato público do app.
pub struct CitizenDataLimits {
    pub max_feed_items: usize,
    pub max_ranking_items: usize,
}

impl CitizenDataConfig {
    /// Carrega a configuração de dados adequada ao ambiente atual.
    pub fn load() -> Result<Self> {
        let path = resolver_caminho_config_ambiente(Path::new(MANIFEST_DIR), "citizen_data");
        carregar_config_toml(&path)
    }

    pub fn project_root(&self) -> PathBuf {
        resolve_relative(Path::new(MANIFEST_DIR), &self.paths.project_root)
    }

    /// Caminho absoluto do CSV consolidado da Câmara.
    pub fn camara_csv_path(&self) -> PathBuf {
        resolve_relative(&self.project_root(), &self.paths.camara_csv)
    }

    /// Caminho absoluto do diretório com os JSONs do Senado.
    pub fn senado_dir_path(&self) -> PathBuf {
        resolve_relative(&self.project_root(), &self.paths.senado_dir)
    }

    /// Caminho absoluto da dimensão JSONL de fornecedores.
    pub fn suppliers_jsonl_path(&self) -> PathBuf {
        resolve_relative(&self.project_root(), &self.paths.suppliers_jsonl)
    }
}

/// Resolve um caminho relativo a uma base conhecida, preservando caminhos absolutos.
fn resolve_relative(base: &Path, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        return path;
    }

    base.join(path)
}
