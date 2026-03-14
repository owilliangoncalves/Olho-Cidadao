//! Utilitários compartilhados de carregamento de configuração.

use std::{
    fs,
    path::{Path, PathBuf},
};

use anyhow::{Context, Result};
use serde::de::DeserializeOwned;

/// Carrega e desserializa um arquivo TOML em um tipo fortemente tipado.
pub(crate) fn carregar_config_toml<T>(path: &Path) -> Result<T>
where
    T: DeserializeOwned,
{
    let raw = fs::read_to_string(path)
        .with_context(|| format!("nao foi possivel ler {}", path.display()))?;

    toml::from_str(&raw).with_context(|| format!("nao foi possivel interpretar {}", path.display()))
}

/// Resolve o arquivo de configuração TOML mais adequado para o ambiente atual.
pub(crate) fn resolver_caminho_config_ambiente(manifest_dir: &Path, stem: &str) -> PathBuf {
    let profile = perfil_atual();
    let config_dir = manifest_dir.join("config");
    let profile_path = config_dir.join(format!("{stem}.{profile}.toml"));
    if profile_path.exists() {
        return profile_path;
    }

    config_dir.join(format!("{stem}.development.toml"))
}

fn perfil_atual() -> String {
    if cfg!(test) {
        return "test".to_string();
    }

    std::env::var("LOCO_ENV")
        .or_else(|_| std::env::var("APP_ENV"))
        .unwrap_or_else(|_| "development".to_string())
}
