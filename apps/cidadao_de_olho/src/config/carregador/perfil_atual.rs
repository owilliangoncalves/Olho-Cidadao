/// Resolve o perfil atual da aplicação a partir do ambiente.
pub(crate) fn perfil_atual() -> String {
    if cfg!(test) {
        return "test".to_string();
    }

    std::env::var("LOCO_ENV")
        .or_else(|_| std::env::var("APP_ENV"))
        .unwrap_or_else(|_| "development".to_string())
}
