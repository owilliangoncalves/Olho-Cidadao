/// Versão exposta pela aplicação, enriquecida com SHA quando disponível.
pub(super) fn app_version() -> String {
    format!(
        "{} ({})",
        env!("CARGO_PKG_VERSION"),
        option_env!("BUILD_SHA")
            .or(option_env!("GITHUB_SHA"))
            .unwrap_or("dev")
    )
}
