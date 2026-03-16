use loco_rs::{
    app::{AppContext, Initializer},
    Result,
};

/// Inicializadores extras do app.
pub(super) async fn initializers(_ctx: &AppContext) -> Result<Vec<Box<dyn Initializer>>> {
    Ok(vec![])
}
