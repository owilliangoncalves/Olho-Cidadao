use std::{fs, path::Path};

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
