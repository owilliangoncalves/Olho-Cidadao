use std::path::{Path, PathBuf};

/// Resolve um caminho relativo a uma base conhecida, preservando caminhos absolutos.
pub fn resolve_relative(base: &Path, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        return path;
    }

    base.join(path)
}
