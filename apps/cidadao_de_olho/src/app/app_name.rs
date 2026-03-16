/// Nome canônico da aplicação.
pub(super) fn app_name() -> &'static str {
    env!("CARGO_CRATE_NAME")
}
