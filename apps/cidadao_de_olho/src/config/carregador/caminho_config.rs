use std::path::{Path, PathBuf};

/// Resolve um arquivo TOML dentro do diretório `config` da aplicação.
#[must_use]
pub(crate) fn caminho_config(manifest_dir: &Path, file_name: &str) -> PathBuf {
    manifest_dir.join("config").join(file_name)
}
