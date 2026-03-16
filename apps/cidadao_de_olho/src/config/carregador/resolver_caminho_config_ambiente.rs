use std::path::{Path, PathBuf};

use super::{caminho_config::caminho_config, perfil_atual::perfil_atual};

/// Resolve o arquivo de configuração TOML mais adequado para o ambiente atual.
pub(crate) fn resolver_caminho_config_ambiente(manifest_dir: &Path, stem: &str) -> PathBuf {
    let profile = perfil_atual();
    let config_dir = caminho_config(manifest_dir, "").with_file_name("config");
    let profile_path = config_dir.join(format!("{stem}.{profile}.toml"));
    if profile_path.exists() {
        return profile_path;
    }

    config_dir.join(format!("{stem}.development.toml"))
}
